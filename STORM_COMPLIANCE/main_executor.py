#!/usr/bin/env python3
"""
STORM-COMPLIANCE Main Executor
Unified system that chains violation analysis and automated reporting
"""

import asyncio
import logging
import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

from modules.violation_analyzer import ViolationAnalyzer
from compliance_report_distributor import ComplianceReportDistributor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('storm_compliance.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class StormComplianceSystem:
    """Main system that orchestrates analysis and reporting"""
    
    def __init__(self, api_id: int, api_hash: str, sessions_dir: str = "sessions"):
        self.api_id = api_id
        self.api_hash = api_hash
        self.sessions_dir = sessions_dir
        self.analyzer = None
        self.distributor = None
        self.results_dir = "results"
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create necessary directories"""
        os.makedirs(self.sessions_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)
    
    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing STORM-COMPLIANCE system...")
        
        # Initialize analyzer
        self.analyzer = ViolationAnalyzer(self.api_id, self.api_hash)
        logger.info("Violation analyzer initialized")
        
        # Initialize distributor
        self.distributor = ComplianceReportDistributor(self.api_id, self.api_hash, self.sessions_dir)
        await self.distributor.initialize_sessions()
        logger.info("Report distributor initialized")
        
        if not self.distributor.clients:
            logger.error("No active sessions found. Please add session files to sessions/ directory")
            return False
        
        return True
    
    async def analyze_and_report(self, channel_username: str, 
                                 scan_limit: int = 100, 
                                 auto_report: bool = True) -> Dict[str, Any]:
        """
        Complete workflow: Analyze channel and automatically report violations
        
        Args:
            channel_username: Target channel username
            scan_limit: Number of messages to scan
            auto_report: Whether to automatically send reports
            
        Returns:
            Complete results dictionary
        """
        start_time = time.time()
        
        logger.info(f"Starting compliance workflow for {channel_username}")
        
        results = {
            'channel': channel_username,
            'scan_limit': scan_limit,
            'auto_report': auto_report,
            'start_time': datetime.now().isoformat(),
            'analysis': None,
            'reporting': None,
            'statistics': None,
            'errors': []
        }
        
        try:
            # Step 1: Analyze channel for violations
            logger.info("Step 1: Analyzing channel for violations...")
            analysis_results = await self.analyzer.analyze_channel(channel_username, scan_limit)
            results['analysis'] = analysis_results
            
            if 'error' in analysis_results:
                results['errors'].append(f"Analysis error: {analysis_results['error']}")
                return results
            
            # Count violations
            total_violations = sum(len(violations) for violations in analysis_results['violations'].values())
            logger.info(f"Analysis complete: {total_violations} violations found")
            
            if total_violations == 0:
                logger.info("No violations found, skipping reporting phase")
                results['reporting'] = {'message': 'No violations to report'}
                results['statistics'] = self.distributor.get_statistics()
                return results
            
            # Step 2: Send compliance reports
            if auto_report:
                logger.info("Step 2: Sending compliance reports...")
                reporting_results = await self.distributor.send_reports_from_analysis(
                    channel_username, analysis_results
                )
                results['reporting'] = reporting_results
            else:
                logger.info("Auto-reporting disabled, skipping reporting phase")
                results['reporting'] = {'message': 'Auto-reporting disabled'}
            
            # Step 3: Get final statistics
            results['statistics'] = self.distributor.get_statistics()
            
        except Exception as e:
            error_msg = f"Workflow error: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        finally:
            results['end_time'] = datetime.now().isoformat()
            results['duration_seconds'] = time.time() - start_time
            
            # Save results
            self.save_results(results)
        
        return results
    
    def save_results(self, results: Dict[str, Any]):
        """Save results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{results['channel'].replace('@', '')}_{timestamp}.json"
        filepath = os.path.join(self.results_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Results saved to: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save results: {str(e)}")
    
    async def continuous_monitoring(self, channel_username: str, 
                                   interval_minutes: int = 30,
                                   scan_limit: int = 50) -> None:
        """
        Continuous monitoring mode
        
        Args:
            channel_username: Channel to monitor
            interval_minutes: Minutes between scans
            scan_limit: Messages to scan each time
        """
        logger.info(f"Starting continuous monitoring for {channel_username}")
        logger.info(f"Scan interval: {interval_minutes} minutes, Scan limit: {scan_limit} messages")
        
        while True:
            try:
                logger.info(f"Running scan at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                results = await self.analyze_and_report(channel_username, scan_limit, True)
                
                # Log summary
                if results['analysis']:
                    total_violations = sum(len(v) for v in results['analysis']['violations'].values())
                    logger.info(f"Scan complete: {total_violations} violations found")
                
                if results['reporting'] and 'successful_reports' in results['reporting']:
                    logger.info(f"Reports sent: {results['reporting']['successful_reports']} successful")
                
                # Wait for next scan
                logger.info(f"Waiting {interval_minutes} minutes until next scan...")
                await asyncio.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("Continuous monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {str(e)}")
                logger.info("Waiting 5 minutes before retry...")
                await asyncio.sleep(300)
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.distributor:
            await self.distributor.cleanup()
        logger.info("System cleanup completed")

def load_config():
    """Load configuration from environment variables"""
    config = {}
    
    # Required
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    if not api_id or not api_hash:
        logger.error("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set")
        return None
    
    try:
        config['api_id'] = int(api_id)
    except ValueError:
        logger.error("TELEGRAM_API_ID must be an integer")
        return None
    
    config['api_hash'] = api_hash
    
    # Optional
    config['sessions_dir'] = os.getenv('SESSIONS_DIR', 'sessions')
    config['results_dir'] = os.getenv('RESULTS_DIR', 'results')
    
    return config

async def main():
    """Main entry point"""
    # Load configuration
    config = load_config()
    if not config:
        return
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='STORM-COMPLIANCE System')
    parser.add_argument('--channel', required=True, help='Target channel username')
    parser.add_argument('--limit', type=int, default=100, help='Messages to scan')
    parser.add_argument('--no-report', action='store_true', help='Skip automatic reporting')
    parser.add_argument('--continuous', type=int, metavar='MINUTES', 
                       help='Enable continuous monitoring with specified interval')
    parser.add_argument('--sessions-dir', default='sessions', help='Sessions directory')
    
    args = parser.parse_args()
    
    # Initialize system
    system = StormComplianceSystem(
        config['api_id'], 
        config['api_hash'], 
        args.sessions_dir
    )
    
    try:
        # Initialize components
        if not await system.initialize():
            logger.error("System initialization failed")
            return
        
        # Run based on mode
        if args.continuous:
            # Continuous monitoring mode
            await system.continuous_monitoring(args.channel, args.continuous, args.limit)
        else:
            # Single scan mode
            results = await system.analyze_and_report(
                args.channel, 
                args.limit, 
                not args.no_report
            )
            
            # Print summary
            print("\n" + "="*60)
            print("STORM-COMPLIANCE EXECUTION SUMMARY")
            print("="*60)
            print(f"Channel: {results['channel']}")
            print(f"Duration: {results['duration_seconds']:.2f} seconds")
            
            if results['analysis']:
                total_violations = sum(len(v) for v in results['analysis']['violations'].values())
                print(f"Violations Found: {total_violations}")
                
                for category, violations in results['analysis']['violations'].items():
                    if violations:
                        print(f"  - {category}: {len(violations)} violations")
            
            if results['reporting']:
                if 'successful_reports' in results['reporting']:
                    print(f"Reports Sent: {results['reporting']['successful_reports']}/{results['reporting']['total_reports']}")
                    print(f"Success Rate: {(results['reporting']['successful_reports']/results['reporting']['total_reports']*100):.1f}%")
            
            if results['errors']:
                print(f"Errors: {len(results['errors'])}")
                for error in results['errors']:
                    print(f"  - {error}")
            
            print("="*60)
    
    except KeyboardInterrupt:
        logger.info("Operation stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    finally:
        await system.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
