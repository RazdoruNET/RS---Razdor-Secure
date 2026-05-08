#!/usr/bin/env python3
"""
SQL Injection Auditor - Main Application
CASCADE SWE-1.5 SQL Injection Automation Module
"""

import argparse
import asyncio
import logging
import requests
import time
import hashlib
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from modules.crawler import WebCrawler, InputVector, VectorAnalyzer
from modules.payload_engine import PayloadGenerator, PayloadOptimizer, DatabaseType, InjectionType
from modules.analysis_engine import VulnerabilityScanner, Vulnerability
from modules.verification import VulnerabilityVerifier, VerificationResult
from modules.waf_bypass import WAFBypassEngine
from modules.reporting import ReportGenerator, ScanSummary
from modules.security import SecurityManager, SecurityLevel
from modules.enterprise_integration import (
    EnterpriseSecurityBridge, EnterpriseVulnerabilityScanner, 
    EnterpriseConfigurationManager
)

class SQLInjectionAuditor:
    """Main SQL injection auditor class"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = self._setup_logging()
        
        # Initialize enterprise security controls FIRST
        self.enterprise_config = EnterpriseConfigurationManager()
        
        if self.enterprise_config.is_enterprise_enabled():
            self.logger.info("🔐 Enterprise Security Mode: ENABLED")
            self.security_bridge = EnterpriseSecurityBridge(use_enterprise=True)
            self.enterprise_scanner = None  # Will be created with security bridge
        else:
            self.logger.info("🔒 Legacy Security Mode: ENABLED")
            self.security_manager = SecurityManager(config.get('security_config', 'security_config.json'))
            self.security_bridge = EnterpriseSecurityBridge(use_enterprise=False)
            self.enterprise_scanner = None
        
        self.auth_token = config.get('auth_token')
        
        # Initialize components
        self.session = self._setup_session()
        self.crawler = WebCrawler(
            delay=config.get('crawl_delay', 1.0),
            user_agent=config.get('user_agent'),
            respect_robots=config.get('respect_robots', True)
        )
        self.payload_generator = PayloadGenerator()
        self.payload_optimizer = PayloadOptimizer()
        
        # Initialize scanner based on security mode
        if self.enterprise_config.is_enterprise_enabled():
            self.scanner = None  # Will use enterprise scanner
        else:
            self.scanner = VulnerabilityScanner(self.session, config.get('timeout', 30))
        
        self.verifier = VulnerabilityVerifier(self.session, config.get('timeout', 30))
        self.waf_bypass = WAFBypassEngine()
        self.report_generator = ReportGenerator(config.get('output_dir', 'reports'))
        
        self.vulnerabilities: List[Vulnerability] = []
        self.verification_results: List[VerificationResult] = []
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create file handler
        file_handler = logging.FileHandler('sql_injection_auditor.log')
        file_handler.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
    
    def _setup_session(self) -> requests.Session:
        """Setup HTTP session with configuration"""
        session = requests.Session()
        
        # Set headers
        session.headers.update({
            'User-Agent': self.config.get('user_agent', 'SQLiAuditor/1.0'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Set proxies if configured
        if self.config.get('proxies'):
            session.proxies.update(self.config['proxies'])
        
        # Set timeout
        session.timeout = self.config.get('timeout', 30)
        
        return session
    
    def audit_target(self, target_url: str, scan_mode: str = 'active') -> Dict[str, Any]:
        """Perform complete SQL injection audit"""
        start_time = time.time()
        self.logger.info(f"Starting SQL injection audit for: {target_url}")
        
        # MANDATORY: Enterprise/Legacy Security authorization check
        user_context = {
            "auth_token": self.auth_token,
            "user_id": "system",
            "session_id": hashlib.sha256(os.urandom(16)).hexdigest()[:16]
        }
        
        authorized, auth_msg, decision = self.security_bridge.authorize_execution(
            target_url, 'execute_requests', None, user_context
        )
        
        if not authorized:
            error_msg = f"🔐 SECURITY VIOLATION: {auth_msg}"
            self.logger.error(error_msg)
            self.security_bridge.log_operation(
                "security_denied_enterprise", target_url, "audit_start",
                metadata={"reason": auth_msg, "decision_id": decision.decision_id if decision else None}
            )
            return {
                'target': target_url,
                'status': 'security_denied',
                'error': error_msg,
                'vulnerabilities_found': 0,
                'duration': time.time() - start_time,
                'security_mode': 'enterprise' if self.enterprise_config.is_enterprise_enabled() else 'legacy'
            }
        
        try:
            # Step 1: Crawl and discover input vectors
            self.logger.info("Phase 1: Crawling and discovering input vectors")
            input_vectors = self._discover_input_vectors(target_url, scan_mode)
            
            if not input_vectors:
                self.logger.warning("No input vectors discovered")
                return self._create_audit_result(target_url, start_time, input_vectors)
            
            # Step 2: Analyze and prioritize vectors
            self.logger.info("Phase 2: Analyzing and prioritizing vectors")
            vector_analysis = self._analyze_vectors(input_vectors)
            
            # Step 3: Scan for vulnerabilities
            self.logger.info("Phase 3: Scanning for SQL injection vulnerabilities")
            self._scan_vulnerabilities_enterprise(vector_analysis, user_context)
            
            # Step 4: Verify findings
            if self.config.get('verify_vulnerabilities', True):
                self.logger.info("Phase 4: Verifying vulnerability findings")
                self._verify_vulnerabilities()
            
            # Step 5: Generate reports
            self.logger.info("Phase 5: Generating security reports")
            report_files = self._generate_reports(target_url, start_time, input_vectors)
            
            return self._create_audit_result(target_url, start_time, input_vectors, report_files)
            
        except Exception as e:
            self.logger.error(f"Audit failed: {e}")
            return {
                'target': target_url,
                'status': 'failed',
                'error': str(e),
                'vulnerabilities_found': 0,
                'duration': time.time() - start_time
            }
    
    def _discover_input_vectors(self, target_url: str, scan_mode: str) -> List[InputVector]:
        """Discover input vectors through crawling or manual analysis"""
        if scan_mode == 'passive':
            # Passive mode - analyze only the provided URL
            vectors = []
            parsed = urlparse(target_url)
            if parsed.query:
                vector = InputVector(
                    url=target_url,
                    method='GET',
                    params=dict(pair.split('=') for pair in parsed.query.split('&') if '=' in pair)
                )
                vectors.append(vector)
            return vectors
        else:
            # Active mode - crawl the website
            return self.crawler.crawl_domain(
                target_url, 
                max_depth=self.config.get('crawl_depth', 3)
            )
    
    def _analyze_vectors(self, input_vectors: List[InputVector]) -> Dict[str, Any]:
        """Analyze and prioritize input vectors"""
        analyzer = VectorAnalyzer()
        return analyzer.analyze_vectors(input_vectors)
    
    def _scan_vulnerabilities_enterprise(self, vector_analysis: Dict[str, Any], user_context: Dict):
        """Scan for SQL injection vulnerabilities with enterprise security"""
        # Determine database types to test
        db_types = self._get_database_types()
        
        # Get all vectors to test
        all_vectors = (
            vector_analysis.get('high_risk', []) +
            vector_analysis.get('medium_risk', []) +
            vector_analysis.get('low_risk', [])
        )
        
        # Use enterprise scanner if available
        if self.enterprise_config.is_enterprise_enabled():
            self.enterprise_scanner = EnterpriseVulnerabilityScanner(
                self.session, 
                self.config.get('timeout', 30),
                self.security_bridge
            )
        
        for vector in all_vectors:
            self.logger.info(f"🔍 Testing vector: {vector}")
            
            # Get parameters to test
            if vector.method == 'GET':
                params = vector.params
            else:
                params = vector.data
            
            for param in params.keys():
                for db_type in db_types:
                    # Test different injection types
                    for injection_type in [InjectionType.ERROR_BASED, InjectionType.BOOLEAN_BASED, 
                                         InjectionType.TIME_BASED, InjectionType.UNION_BASED]:
                        
                        # Generate payloads
                        payloads = self.payload_generator.generate_all_payloads(db_type)
                        type_payloads = payloads.get(injection_type.value, [])
                        
                        # Optimize payload order
                        optimized_payloads = self.payload_optimizer.optimize_payload_order(
                            type_payloads, 
                            strategy=self.config.get('payload_strategy', 'effectiveness')
                        )
                        
                        # Enterprise scan with security enforcement
                        if self.enterprise_config.is_enterprise_enabled():
                            vulnerabilities = self.enterprise_scanner.scan_parameter_enterprise(
                                vector.url, param, optimized_payloads, 
                                injection_type.value, db_type.value, user_context
                            )
                        else:
                            # Legacy scan with security checks
                            vulnerabilities = self.scanner.scan_parameter(
                                vector.url, param, optimized_payloads, injection_type, db_type
                            )
                        
                        self.vulnerabilities.extend(vulnerabilities)
                        
                        # If vulnerability found, try WAF bypass
                        if vulnerabilities and self.config.get('enable_waf_bypass', True):
                            if self.enterprise_config.is_enterprise_enabled():
                                self._attempt_waf_bypass_enterprise(vector, param, injection_type, db_type, user_context)
                            else:
                                self._attempt_waf_bypass(vector, param, injection_type, db_type)
    
    def _scan_vulnerabilities(self, vector_analysis: Dict[str, Any]):
        """Legacy scan for SQL injection vulnerabilities"""
        # Fallback to legacy scanning
        # Determine database types to test
        db_types = self._get_database_types()
        
        # Get all vectors to test
        all_vectors = (
            vector_analysis.get('high_risk', []) +
            vector_analysis.get('medium_risk', []) +
            vector_analysis.get('low_risk', [])
        )
        
        for vector in all_vectors:
            self.logger.info(f"Testing vector: {vector}")
            
            # Get parameters to test
            if vector.method == 'GET':
                params = vector.params
            else:
                params = vector.data
            
            for param in params.keys():
                for db_type in db_types:
                    # Test different injection types
                    for injection_type in [InjectionType.ERROR_BASED, InjectionType.BOOLEAN_BASED, 
                                         InjectionType.TIME_BASED, InjectionType.UNION_BASED]:
                        
                        # Generate payloads
                        payloads = self.payload_generator.generate_all_payloads(db_type)
                        type_payloads = payloads.get(injection_type.value, [])
                        
                        # Optimize payload order
                        optimized_payloads = self.payload_optimizer.optimize_payload_order(
                            type_payloads, 
                            strategy=self.config.get('payload_strategy', 'effectiveness')
                        )
                        
                        # Scan with payloads
                        vulnerabilities = self.scanner.scan_parameter(
                            vector.url, param, optimized_payloads, injection_type, db_type
                        )
                        
                        self.vulnerabilities.extend(vulnerabilities)
                        
                        # If vulnerability found, try WAF bypass
                        if vulnerabilities and self.config.get('enable_waf_bypass', True):
                            self._attempt_waf_bypass(vector, param, injection_type, db_type)
    
    def _attempt_waf_bypass(self, vector: InputVector, param: str, 
                           injection_type: InjectionType, db_type: DatabaseType):
        """Attempt WAF bypass techniques"""
        if not self.config.get('enable_waf_bypass', True):
            return
        # Get a basic payload to test WAF response
        basic_payloads = {
            InjectionType.ERROR_BASED: ["'"],
            InjectionType.BOOLEAN_BASED: ["' AND 1=1 -- "],
            InjectionType.TIME_BASED: ["' AND SLEEP(5) -- "],
            InjectionType.UNION_BASED: ["' UNION SELECT 1 -- "]
        }
        
        test_payload = basic_payloads.get(injection_type, ["'"])[0]
        
        # Send test payload to detect WAF
        try:
            parsed_url = urlparse(vector.url)
            params = dict(pair.split('=') for pair in parsed_url.query.split('&') if '=' in pair)
            params[param] = [test_payload]
            
            query_string = '&'.join([f"{k}={v[0]}" for k, v in params.items()])
            test_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{query_string}"
            
            response = self.session.get(test_url, timeout=10)
            
            # Analyze WAF response
            waf_analysis = self.waf_bypass.analyze_waf_response(
                dict(response.headers), 
                response.text
            )
            
            if waf_analysis['waf_detected']:
                self.logger.info(f"WAF detected: {waf_analysis['waf_type']}")
                
                # Generate bypass payloads
                bypass_payloads = self.waf_bypass.bypass_payload(
                    test_payload,
                    dict(response.headers),
                    response.text,
                    waf_analysis['waf_type']
                )
                
                # Test bypass payloads
                for bypass_payload in bypass_payloads[:10]:  # Limit to avoid too many requests
                    vulnerabilities = self.scanner.scan_parameter(
                        vector.url, param, [bypass_payload], injection_type, db_type
                    )
                    self.vulnerabilities.extend(vulnerabilities)
                    
                    if vulnerabilities:
                        self.logger.info(f"WAF bypass successful with payload: {bypass_payload}")
                        break
                        
        except Exception as e:
            self.logger.error(f"Error in WAF bypass attempt: {e}")
    
    def _attempt_waf_bypass_enterprise(self, vector: InputVector, param: str,
                                     injection_type: InjectionType, db_type: DatabaseType,
                                     user_context: Dict):
        """Attempt WAF bypass techniques with enterprise security"""
        if not self.config.get('enable_waf_bypass', True):
            return
        
        self.logger.info(f"Attempting WAF bypass for {param} (enterprise)")
        
        # Get basic payload to test WAF response
        basic_payloads = {
            InjectionType.ERROR_BASED: ["'"],
            InjectionType.BOOLEAN_BASED: ["' AND 1=1 -- "],
            InjectionType.TIME_BASED: ["' AND SLEEP(5) -- "],
            InjectionType.UNION_BASED: ["' UNION SELECT 1 -- "]
        }
        
        test_payload = basic_payloads.get(injection_type, ["'"])[0]
        
        # Send test payload to detect WAF
        try:
            parsed_url = urlparse(vector.url)
            params = dict(pair.split('=') for pair in parsed_url.query.split('&') if '=' in pair)
            params[param] = [test_payload]
            
            query_string = '&'.join([f"{k}={v[0]}" for k, v in params.items()])
            test_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{query_string}"
            
            response = self.session.get(test_url, timeout=10)
            
            # Analyze WAF response
            waf_analysis = self.waf_bypass.analyze_waf_response(
                dict(response.headers), 
                response.text
            )
            
            if waf_analysis['waf_detected']:
                self.logger.info(f"WAF detected: {waf_analysis['waf_type']}")
                
                # Generate bypass payloads
                bypass_payloads = self.waf_bypass.bypass_payload(
                    test_payload,
                    dict(response.headers),
                    response.text,
                    waf_analysis['waf_type']
                )
                
                # Test bypass payloads with enterprise security
                for bypass_payload in bypass_payloads[:10]:  # Limit to avoid too many requests
                    vulnerabilities = self.enterprise_scanner.scan_parameter_enterprise(
                        vector.url, param, [bypass_payload], 
                        injection_type.value, db_type.value, user_context
                    )
                    self.vulnerabilities.extend(vulnerabilities)
                    
                    if vulnerabilities:
                        self.logger.info(f"WAF bypass successful with payload: {bypass_payload}")
                        break
                        
        except Exception as e:
            self.logger.error(f"Error in enterprise WAF bypass attempt: {e}")
    
    def _verify_vulnerabilities(self):
        """Verify discovered vulnerabilities"""
        for vulnerability in self.vulnerabilities:
            try:
                verification_result = self.verifier.verify_vulnerability(vulnerability)
                self.verification_results.append(verification_result)
                
                # Log verification result
                self.logger.info(
                    f"Verification {verification_result.status.value}: "
                    f"{vulnerability.url} - {vulnerability.parameter} "
                    f"(confidence: {verification_result.confidence:.2f})"
                )
                
            except Exception as e:
                self.logger.error(f"Error verifying vulnerability: {e}")
    
    def _generate_reports(self, target_url: str, start_time: float, 
                         input_vectors: List[InputVector]) -> List[str]:
        """Generate security reports"""
        # Create scan summary
        scan_summary = ScanSummary(
            scan_date=datetime.now().isoformat(),
            target_url=target_url,
            total_vectors_tested=len(input_vectors),
            vulnerabilities_found=len(self.vulnerabilities),
            high_risk_vulnerabilities=sum(1 for v in self.vulnerabilities if v.confidence >= 0.8),
            medium_risk_vulnerabilities=sum(1 for v in self.vulnerabilities if 0.5 <= v.confidence < 0.8),
            low_risk_vulnerabilities=sum(1 for v in self.vulnerabilities if v.confidence < 0.5),
            scan_duration=time.time() - start_time,
            databases_detected=list(set(v.database_type.value for v in self.vulnerabilities))
        )
        
        # Technical details
        technical_details = {
            'scan_configuration': self.config,
            'input_vectors_count': len(input_vectors),
            'payloads_tested': len(self.vulnerabilities) * 10,  # Estimate
            'verification_enabled': self.config.get('verify_vulnerabilities', True),
            'waf_bypass_enabled': self.config.get('enable_waf_bypass', True)
        }
        
        # Generate reports
        formats = self.config.get('report_formats', ['json'])
        if self.config.get('generate_pdf', False):
            formats.append('pdf')
        
        return self.report_generator.generate_report(
            self.vulnerabilities,
            self.verification_results,
            scan_summary,
            technical_details,
            formats
        )
    
    def _get_database_types(self) -> List[DatabaseType]:
        """Get database types to test"""
        configured_types = self.config.get('database_types', ['mysql', 'postgresql', 'mssql'])
        type_mapping = {
            'mysql': DatabaseType.MYSQL,
            'postgresql': DatabaseType.POSTGRESQL,
            'mssql': DatabaseType.MSSQL,
            'oracle': DatabaseType.ORACLE,
            'sqlite': DatabaseType.SQLITE
        }
        
        return [type_mapping.get(db_type.lower(), DatabaseType.MYSQL) 
                for db_type in configured_types if db_type.lower() in type_mapping]
    
    def _create_audit_result(self, target_url: str, start_time: float, 
                            input_vectors: List[InputVector], 
                            report_files: List[str] = None) -> Dict[str, Any]:
        """Create audit result summary"""
        return {
            'target': target_url,
            'status': 'completed',
            'vulnerabilities_found': len(self.vulnerabilities),
            'vectors_tested': len(input_vectors),
            'duration': time.time() - start_time,
            'high_risk': sum(1 for v in self.vulnerabilities if v.confidence >= 0.8),
            'medium_risk': sum(1 for v in self.vulnerabilities if 0.5 <= v.confidence < 0.8),
            'low_risk': sum(1 for v in self.vulnerabilities if v.confidence < 0.5),
            'report_files': report_files or [],
            'verification_results': len(self.verification_results)
        }

def load_config(config_file: str = None) -> Dict[str, Any]:
    """Load configuration from file or defaults"""
    default_config = {
        'crawl_delay': 1.0,
        'crawl_depth': 3,
        'timeout': 30,
        'user_agent': 'SQLiAuditor/1.0 (Security Audit Tool)',
        'respect_robots': True,
        'database_types': ['mysql', 'postgresql', 'mssql'],
        'payload_strategy': 'effectiveness',
        'verify_vulnerabilities': True,
        'enable_waf_bypass': True,
        'output_dir': 'reports',
        'report_formats': ['json'],
        'generate_pdf': False,
        'proxies': None
    }
    
    if config_file:
        try:
            import json
            with open(config_file, 'r') as f:
                user_config = json.load(f)
            default_config.update(user_config)
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")
    
    return default_config

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='SQL Injection Auditor - Automated SQL Injection Security Testing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python main.py -u http://example.com
  python main.py -u http://example.com --mode passive
  python main.py -u http://example.com --config config.json
  python main.py -u http://example.com --databases mysql postgresql
        '''
    )
    
    parser.add_argument('-u', '--url', required=True, 
                       help='Target URL to audit')
    parser.add_argument('--mode', choices=['active', 'passive'], default='active',
                       help='Scan mode: active (crawl) or passive (single URL)')
    parser.add_argument('--config', 
                       help='Configuration file path (JSON)')
    parser.add_argument('--databases', nargs='+', 
                       choices=['mysql', 'postgresql', 'mssql', 'oracle', 'sqlite'],
                       default=['mysql', 'postgresql', 'mssql'],
                       help='Database types to test')
    parser.add_argument('--depth', type=int, default=3,
                       help='Crawling depth (active mode only)')
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay between requests (seconds)')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Request timeout (seconds)')
    parser.add_argument('--no-verify', action='store_true',
                       help='Skip vulnerability verification')
    parser.add_argument('--no-waf-bypass', action='store_true',
                       help='Disable WAF bypass attempts')
    parser.add_argument('--pdf', action='store_true',
                       help='Generate PDF report (requires reportlab)')
    parser.add_argument('--output-dir', default='reports',
                       help='Output directory for reports')
    parser.add_argument('--proxy',
                       help='Proxy URL (e.g., http://127.0.0.1:8080)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override config with command line arguments
    config.update({
        'crawl_depth': args.depth,
        'crawl_delay': args.delay,
        'timeout': args.timeout,
        'verify_vulnerabilities': not args.no_verify,
        'enable_waf_bypass': not args.no_waf_bypass,
        'generate_pdf': args.pdf,
        'output_dir': args.output_dir,
        'database_types': args.databases
    })
    
    if args.proxy:
        config['proxies'] = {
            'http': args.proxy,
            'https': args.proxy
        }
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create auditor and run scan
    auditor = SQLInjectionAuditor(config)
    
    try:
        result = auditor.audit_target(args.url, args.mode)
        
        # Print results
        print("\n" + "="*60)
        print("SQL INJECTION AUDIT RESULTS")
        print("="*60)
        print(f"Target: {result['target']}")
        print(f"Status: {result['status']}")
        print(f"Duration: {result['duration']:.2f} seconds")
        print(f"Vectors Tested: {result['vectors_tested']}")
        print(f"Vulnerabilities Found: {result['vulnerabilities_found']}")
        print(f"  High Risk: {result['high_risk']}")
        print(f"  Medium Risk: {result['medium_risk']}")
        print(f"  Low Risk: {result['low_risk']}")
        
        if result.get('report_files'):
            print(f"\nReports generated:")
            for report_file in result['report_files']:
                print(f"  - {report_file}")
        
        if result['status'] == 'failed':
            print(f"Error: {result.get('error', 'Unknown error')}")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\nAudit interrupted by user")
        return 1
    except Exception as e:
        print(f"\nAudit failed: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
