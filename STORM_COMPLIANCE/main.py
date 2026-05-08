#!/usr/bin/env python3
"""
Enterprise Content Protection & Compliance System
STORM-COMPLIANCE Framework

A comprehensive system for copyright protection, ToS monitoring, and compliance automation.
"""

import asyncio
import logging
import argparse
import json
import os
from typing import Dict, Any, List
from datetime import datetime

from config.settings import Config
from modules.violation_analyzer import ViolationAnalyzer
from modules.compliance_reporter import ComplianceReporter
from modules.stress_tester import ModerationStressTester
from modules.dmca_engine import DMCAEngine

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class StormComplianceSystem:
    """Main orchestrator for the STORM-COMPLIANCE framework"""
    
    def __init__(self):
        self.config = Config()
        self.violation_analyzer = None
        self.compliance_reporter = None
        self.stress_tester = None
        self.dmca_engine = None
        
    async def initialize(self):
        """Initialize all system components"""
        logger.info("Initializing STORM-COMPLIANCE system...")
        
        # Initialize violation analyzer
        if self.config.API_ID and self.config.API_HASH:
            self.violation_analyzer = ViolationAnalyzer(
                self.config.API_ID, 
                self.config.API_HASH
            )
            logger.info("Violation analyzer initialized")
        
        # Initialize compliance reporter
        session_files = self._get_session_files()
        if session_files:
            self.compliance_reporter = ComplianceReporter(
                self.config.API_ID,
                self.config.API_HASH,
                session_files
            )
            logger.info(f"Compliance reporter initialized with {len(session_files)} sessions")
        
        # Initialize stress tester
        self.stress_tester = ModerationStressTester({
            'use_proxies': False,
            'proxies': []
        })
        logger.info("Stress tester initialized")
        
        # Initialize DMCA engine
        dmca_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'sender_email': os.getenv('DMCA_SENDER_EMAIL'),
            'sender_password': os.getenv('DMCA_SENDER_PASSWORD'),
            'template_dir': 'templates'
        }
        self.dmca_engine = DMCAEngine(dmca_config)
        logger.info("DMCA engine initialized")
    
    def _get_session_files(self) -> List[str]:
        """Get list of available session files"""
        session_dir = self.config.SESSION_DIR
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)
            return []
        
        session_files = []
        for file in os.listdir(session_dir):
            if file.endswith('.session'):
                session_files.append(file)
        
        return session_files
    
    async def analyze_channel(self, channel_username: str, limit: int = None) -> Dict[str, Any]:
        """Analyze channel for content violations"""
        if not self.violation_analyzer:
            raise Exception("Violation analyzer not initialized")
        
        logger.info(f"Starting analysis of channel: {channel_username}")
        scan_limit = limit or self.config.SCAN_DEPTH
        
        results = await self.violation_analyzer.analyze_channel(channel_username, scan_limit)
        
        # Save results
        output_file = f"analysis_results/{channel_username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('analysis_results', exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Analysis complete. Results saved to: {output_file}")
        return results
    
    async def submit_compliance_reports(self, channel_username: str, 
                                      analysis_results: Dict[str, Any] = None) -> Dict[str, Any]:
        """Submit compliance reports based on analysis results"""
        if not self.compliance_reporter:
            raise Exception("Compliance reporter not initialized")
        
        if not analysis_results:
            # Run analysis first
            analysis_results = await self.analyze_channel(channel_username)
        
        logger.info(f"Submitting compliance reports for: {channel_username}")
        
        results = await self.compliance_reporter.batch_report_violations(analysis_results)
        
        # Save results
        output_file = f"compliance_reports/{channel_username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('compliance_reports', exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Compliance reports submitted. Results saved to: {output_file}")
        return results
    
    async def run_stress_test(self, target_channel: str, test_type: str = 'load', 
                            duration_minutes: int = 10) -> Dict[str, Any]:
        """Run stress tests against moderation system"""
        if not self.stress_tester:
            raise Exception("Stress tester not initialized")
        
        logger.info(f"Starting {test_type} stress test for: {target_channel}")
        
        if test_type == 'load':
            # Define a mock action function for load testing
            async def mock_action(session, target):
                await asyncio.sleep(random.uniform(0.5, 2.0))
                return {
                    'action': 'mock_request',
                    'success': True,
                    'data': {'response': 'OK'}
                }
            
            results = await self.stress_tester.distributed_load_test(
                target_channel, mock_action, duration_minutes, 5
            )
        
        elif test_type == 'moderation_resilience':
            test_scenarios = [
                {
                    'name': 'Report Flood Test',
                    'type': 'report_flood',
                    'description': 'Test resilience against report flooding',
                    'report_count': 50
                },
                {
                    'name': 'Content Injection Test',
                    'type': 'content_injection',
                    'description': 'Test detection of injected content',
                    'injection_count': 10
                },
                {
                    'name': 'Session Rotation Test',
                    'type': 'session_rotation',
                    'description': 'Test detection of session rotation',
                    'session_count': 20
                }
            ]
            
            results = await self.stress_tester.moderation_resilience_test(
                target_channel, test_scenarios
            )
        
        else:
            raise ValueError(f"Unknown test type: {test_type}")
        
        # Save results
        output_file = f"stress_test_results/{target_channel}_{test_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('stress_test_results', exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Stress test completed. Results saved to: {output_file}")
        return results
    
    async def generate_dmca_notices(self, channel_username: str, 
                                  analysis_results: Dict[str, Any] = None,
                                  copyright_info: Dict[str, Any] = None,
                                  sender_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate DMCA notices for copyright violations"""
        if not self.dmca_engine:
            raise Exception("DMCA engine not initialized")
        
        if not analysis_results:
            analysis_results = await self.analyze_channel(channel_username)
        
        # Default copyright and sender info
        default_copyright = {
            'title': 'Protected Content',
            'author': 'Copyright Holder',
            'registration_number': 'REG-123456',
            'publication_date': '2024-01-01'
        }
        
        default_sender = {
            'name': 'Authorized Agent',
            'email': os.getenv('DMCA_SENDER_EMAIL'),
            'company': 'Content Protection Agency',
            'address': '123 Copyright St, Protection City, PC 12345',
            'phone': '+1-555-123-4567'
        }
        
        copyright_info = copyright_info or default_copyright
        sender_info = sender_info or default_sender
        
        logger.info(f"Generating DMCA notices for: {channel_username}")
        
        # Group violations by channel
        violation_groups = {channel_username: analysis_results['violations']['copyright']}
        
        # Generate notices
        notices = self.dmca_engine.batch_generate_notices(
            violation_groups, copyright_info, sender_info
        )
        
        # Send notices
        if os.getenv('SEND_DMCA_NOTICES', 'false').lower() == 'true':
            sent_results = await self.dmca_engine.send_batch_notices(notices)
        else:
            sent_results = [{'notice': notice, 'sent': False, 'reason': 'Sending disabled'} for notice in notices]
        
        # Create evidence package
        evidence_file = self.dmca_engine.create_evidence_package(
            analysis_results['violations']['copyright']
        )
        
        results = {
            'channel': channel_username,
            'notices_generated': len(notices),
            'notices_sent': len([r for r in sent_results if r.get('success', False)]),
            'evidence_file': evidence_file,
            'notices': notices,
            'sent_results': sent_results
        }
        
        # Save results
        output_file = f"dmca_notices/{channel_username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('dmca_notices', exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"DMCA notices processed. Results saved to: {output_file}")
        return results
    
    async def run_full_compliance_check(self, channel_username: str) -> Dict[str, Any]:
        """Run complete compliance workflow"""
        logger.info(f"Starting full compliance check for: {channel_username}")
        
        start_time = datetime.now()
        
        # Step 1: Analyze violations
        analysis_results = await self.analyze_channel(channel_username)
        
        # Step 2: Submit compliance reports
        compliance_results = await self.submit_compliance_reports(
            channel_username, analysis_results
        )
        
        # Step 3: Generate DMCA notices
        dmca_results = await self.generate_dmca_notices(
            channel_username, analysis_results
        )
        
        # Step 4: Run stress test (optional, based on violations found)
        stress_results = None
        if sum(len(v) for v in analysis_results['violations'].values()) > 10:
            stress_results = await self.run_stress_test(channel_username, 'moderation_resilience', 5)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        final_results = {
            'channel': channel_username,
            'check_duration_seconds': duration,
            'analysis_summary': {
                'total_messages': analysis_results['total_messages'],
                'total_violations': sum(len(v) for v in analysis_results['violations'].values()),
                'violation_types': list(analysis_results['violations'].keys())
            },
            'compliance_summary': {
                'reports_submitted': compliance_results['successful_reports'],
                'categories_reported': list(compliance_results['category_results'].keys())
            },
            'dmca_summary': {
                'notices_generated': dmca_results['notices_generated'],
                'evidence_created': dmca_results['evidence_file']
            },
            'stress_test_summary': stress_results['overall_score'] if stress_results else None,
            'timestamp': end_time.isoformat()
        }
        
        # Save final results
        output_file = f"full_compliance_checks/{channel_username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('full_compliance_checks', exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Full compliance check completed in {duration:.2f} seconds. Results saved to: {output_file}")
        return final_results
    
    async def cleanup(self):
        """Cleanup system resources"""
        if self.compliance_reporter:
            await self.compliance_reporter.cleanup()
        logger.info("System cleanup completed")

async def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='STORM-COMPLIANCE Enterprise Content Protection System')
    parser.add_argument('--channel', required=True, help='Target channel username')
    parser.add_argument('--action', choices=['analyze', 'report', 'stress', 'dmca', 'full'], 
                       default='full', help='Action to perform')
    parser.add_argument('--limit', type=int, help='Number of messages to analyze')
    parser.add_argument('--test-type', choices=['load', 'moderation_resilience'], 
                       default='load', help='Type of stress test')
    parser.add_argument('--duration', type=int, default=10, help='Test duration in minutes')
    
    args = parser.parse_args()
    
    system = StormComplianceSystem()
    
    try:
        await system.initialize()
        
        if args.action == 'analyze':
            results = await system.analyze_channel(args.channel, args.limit)
        elif args.action == 'report':
            results = await system.submit_compliance_reports(args.channel)
        elif args.action == 'stress':
            results = await system.run_stress_test(args.channel, args.test_type, args.duration)
        elif args.action == 'dmca':
            results = await system.generate_dmca_notices(args.channel)
        elif args.action == 'full':
            results = await system.run_full_compliance_check(args.channel)
        
        print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"Error: {str(e)}")
    finally:
        await system.cleanup()

if __name__ == '__main__':
    asyncio.run(main())
