#!/usr/bin/env python3
"""
VK-COMPLIANCE-STRIKE Main Executor
Orchestrates all VK compliance modules for comprehensive content analysis and reporting

Modules:
1. LEGAL-MINING-VK: Content scanning and violation detection
2. VK-REPORT-AUTOMATION: Automated complaint filing
3. SUPPORT-PRESSURE: DMCA claim generation and support pressure
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from modules.legal_mining_vk import LegalMiningVK, Violation
from modules.vk_report_automation import VKReportAutomation, ReportRequest
from modules.support_pressure import SupportPressure, DMCAClaim, SupportTicket

class VKComplianceStrike:
    """Main orchestrator for VK compliance operations"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "./config/vk_compliance_config.json"
        
        # Initialize modules
        self.legal_mining = LegalMiningVK(self.config_path)
        self.report_automation = VKReportAutomation(self.config_path)
        self.support_pressure = SupportPressure(self.config_path)
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Operation state
        self.violations = []
        self.report_requests = []
        self.dmca_claims = []
        self.support_tickets = []
        
    def _setup_logging(self) -> logging.Logger:
        """Setup main logging configuration"""
        logger = logging.getLogger("VKComplianceStrike")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler(
                Path("./data/logs") / "vk_compliance_strike.log",
                encoding='utf-8'
            )
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def run_full_compliance_cycle(self, 
                                 scan_posts: int = 100,
                                 submit_reports: bool = True,
                                 submit_dmca: bool = True,
                                 submit_tickets: bool = True) -> Dict:
        """Run complete compliance cycle"""
        
        self.logger.info("Starting full VK compliance cycle")
        start_time = datetime.now()
        
        results = {
            "scan_results": {},
            "report_results": {},
            "dmca_results": {},
            "ticket_results": {},
            "summary": {},
            "duration": 0,
            "timestamp": start_time.isoformat()
        }
        
        try:
            # Phase 1: Content scanning and violation detection
            self.logger.info("Phase 1: Starting content analysis")
            self.violations = self.legal_mining.scan_group_wall(scan_posts)
            
            results["scan_results"] = {
                "posts_scanned": scan_posts,
                "violations_found": len(self.violations),
                "violation_summary": self.legal_mining.get_violation_summary()
            }
            
            # Save scan results
            scan_results_file = self.legal_mining.save_results()
            self.logger.info(f"Scan results saved to: {scan_results_file}")
            
            if not self.violations:
                self.logger.info("No violations found. Compliance cycle completed.")
                return results
            
            # Phase 2: Generate report requests
            self.logger.info("Phase 2: Generating report requests")
            violations_data = [
                {
                    "post_id": v.post_id,
                    "post_url": v.post_url,
                    "violation_type": v.violation_type,
                    "content_type": v.content_type,
                    "confidence": v.confidence,
                    "evidence": v.evidence
                }
                for v in self.violations
            ]
            
            self.report_requests = self.report_automation.generate_report_requests(violations_data)
            results["scan_results"]["report_requests_generated"] = len(self.report_requests)
            
            # Phase 3: Submit automated reports
            if submit_reports and self.report_requests:
                self.logger.info("Phase 3: Submitting automated reports")
                report_results = self.report_automation.submit_bulk_reports(self.report_requests)
                results["report_results"] = report_results
                
                # Rate limiting between phases
                time.sleep(30)
            
            # Phase 4: Generate DMCA claims
            if submit_dmca:
                self.logger.info("Phase 4: Generating DMCA claims")
                self.dmca_claims = self.support_pressure.generate_brand_protection_claims(violations_data)
                results["dmca_results"]["claims_generated"] = len(self.dmca_claims)
                
                # Submit DMCA claims
                if self.dmca_claims:
                    dmca_results = self.support_pressure.batch_submit_claims(self.dmca_claims)
                    results["dmca_results"].update(dmca_results)
                    
                    # Rate limiting
                    time.sleep(30)
            
            # Phase 5: Generate support tickets
            if submit_tickets:
                self.logger.info("Phase 5: Creating support tickets")
                
                # Create tickets for high-confidence violations
                high_confidence_violations = [
                    v for v in self.violations if v.confidence >= 0.8
                ]
                
                for violation in high_confidence_violations[:10]:  # Limit to 10 tickets
                    ticket = self.support_pressure.create_support_ticket(
                        subject=f"Copyright violation report - {violation.violation_type}",
                        content=f"Violating content found at {violation.post_url}. "
                               f"Violation type: {violation.violation_type}, "
                               f"Confidence: {violation.confidence:.2f}. "
                               f"Evidence: {violation.evidence}",
                        category="copyright",
                        priority="high"
                    )
                    self.support_tickets.append(ticket)
                
                # Submit support tickets
                if self.support_tickets:
                    ticket_results = {
                        "total": len(self.support_tickets),
                        "successful": 0,
                        "failed": 0
                    }
                    
                    for ticket in self.support_tickets:
                        success = self.support_pressure.submit_support_ticket(ticket)
                        if success:
                            ticket_results["successful"] += 1
                        else:
                            ticket_results["failed"] += 1
                        time.sleep(10)  # Rate limiting
                    
                    results["ticket_results"] = ticket_results
            
            # Generate final summary
            duration = (datetime.now() - start_time).total_seconds()
            results["duration"] = duration
            results["summary"] = {
                "total_violations": len(self.violations),
                "reports_submitted": results.get("report_results", {}).get("successful", 0),
                "dmca_claims_submitted": results.get("dmca_results", {}).get("successful", 0),
                "support_tickets_submitted": results.get("ticket_results", {}).get("successful", 0),
                "success_rate": self._calculate_success_rate(results)
            }
            
            self.logger.info(f"Compliance cycle completed in {duration:.2f} seconds")
            self._save_comprehensive_results(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in compliance cycle: {e}")
            results["error"] = str(e)
            return results
    
    def _calculate_success_rate(self, results: Dict) -> float:
        """Calculate overall success rate"""
        total_attempts = 0
        total_successful = 0
        
        for phase in ["report_results", "dmca_results", "ticket_results"]:
            if phase in results:
                total_attempts += results[phase].get("total", 0)
                total_successful += results[phase].get("successful", 0)
        
        if total_attempts == 0:
            return 0.0
        
        return (total_successful / total_attempts) * 100
    
    def _save_comprehensive_results(self, results: Dict):
        """Save comprehensive results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = Path("./data/results") / f"compliance_cycle_{timestamp}.json"
        
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Comprehensive results saved to: {results_file}")
    
    def run_scan_only(self, post_count: int = 100) -> Dict:
        """Run only the content scanning phase"""
        self.logger.info("Running scan-only mode")
        
        violations = self.legal_mining.scan_group_wall(post_count)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "posts_scanned": post_count,
            "violations_found": len(violations),
            "violation_summary": self.legal_mining.get_violation_summary(),
            "violations": [
                {
                    "post_id": v.post_id,
                    "post_url": v.post_url,
                    "violation_type": v.violation_type,
                    "content_type": v.content_type,
                    "confidence": v.confidence,
                    "evidence": v.evidence
                }
                for v in violations
            ]
        }
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = Path("./data/results") / f"scan_only_{timestamp}.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Scan-only results saved to: {results_file}")
        return results
    
    def run_reports_only(self, violations_file: str) -> Dict:
        """Run only the reporting phase using existing violations"""
        self.logger.info("Running reports-only mode")
        
        try:
            with open(violations_file, 'r', encoding='utf-8') as f:
                violations_data = json.load(f)
            
            if isinstance(violations_data, dict) and "violations" in violations_data:
                violations = violations_data["violations"]
            else:
                violations = violations_data
            
            # Generate and submit reports
            report_requests = self.report_automation.generate_report_requests(violations)
            results = self.report_automation.submit_bulk_reports(report_requests)
            
            self.logger.info(f"Reports-only mode completed: {results['successful']}/{results['total']} successful")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in reports-only mode: {e}")
            return {"error": str(e)}
    
    def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up resources")
        self.report_automation.cleanup()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="VK-COMPLIANCE-STRIKE System")
    parser.add_argument("--config", "-c", help="Configuration file path")
    parser.add_argument("--mode", "-m", choices=["full", "scan", "reports"], 
                       default="full", help="Operation mode")
    parser.add_argument("--posts", "-p", type=int, default=100, 
                       help="Number of posts to scan")
    parser.add_argument("--no-reports", action="store_true", 
                       help="Skip report submission")
    parser.add_argument("--no-dmca", action="store_true", 
                       help="Skip DMCA claims")
    parser.add_argument("--no-tickets", action="store_true", 
                       help="Skip support tickets")
    parser.add_argument("--violations-file", "-v", 
                       help="Path to violations file (for reports mode)")
    
    args = parser.parse_args()
    
    # Initialize system
    compliance = VKComplianceStrike(args.config)
    
    try:
        if args.mode == "full":
            results = compliance.run_full_compliance_cycle(
                scan_posts=args.posts,
                submit_reports=not args.no_reports,
                submit_dmca=not args.no_dmca,
                submit_tickets=not args.no_tickets
            )
        elif args.mode == "scan":
            results = compliance.run_scan_only(args.posts)
        elif args.mode == "reports":
            if not args.violations_file:
                print("Error: --violations-file required for reports mode")
                return
            results = compliance.run_reports_only(args.violations_file)
        
        # Print summary
        print("\n=== VK-COMPLIANCE-STRIKE Results ===")
        print(f"Mode: {args.mode}")
        print(f"Timestamp: {results.get('timestamp', 'N/A')}")
        
        if args.mode == "full":
            summary = results.get("summary", {})
            print(f"Total Violations: {summary.get('total_violations', 0)}")
            print(f"Reports Submitted: {summary.get('reports_submitted', 0)}")
            print(f"DMCA Claims Submitted: {summary.get('dmca_claims_submitted', 0)}")
            print(f"Support Tickets Submitted: {summary.get('support_tickets_submitted', 0)}")
            print(f"Success Rate: {summary.get('success_rate', 0):.1f}%")
            print(f"Duration: {results.get('duration', 0):.2f} seconds")
        elif args.mode == "scan":
            print(f"Posts Scanned: {results.get('posts_scanned', 0)}")
            print(f"Violations Found: {results.get('violations_found', 0)}")
        elif args.mode == "reports":
            print(f"Reports Submitted: {results.get('successful', 0)}")
            print(f"Reports Failed: {results.get('failed', 0)}")
        
        print("=====================================\n")
        
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        compliance.cleanup()

if __name__ == "__main__":
    main()
