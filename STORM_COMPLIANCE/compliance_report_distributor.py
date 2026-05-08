#!/usr/bin/env python3
"""
Compliance Report Distributor
Advanced distributed reporting system with session rotation and proper Telegram API integration
"""

import asyncio
import logging
import os
import random
import time
from typing import List, Dict, Any, Optional
from telethon import TelegramClient
from telethon.tl.functions.messages import ReportRequest
from telethon.tl.types import (
    InputPeerChannel, InputPeerUser, InputPeerChat,
    InputReportReasonSpam, InputReportReasonViolence, InputReportReasonCopyright,
    InputReportReasonChildAbuse, InputReportReasonPornography, InputReportReasonFake,
    InputReportReasonOther
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComplianceReportDistributor:
    def __init__(self, api_id: int, api_hash: str, sessions_dir: str = "sessions"):
        self.api_id = api_id
        self.api_hash = api_hash
        self.sessions_dir = sessions_dir
        self.clients: List[TelegramClient] = []
        self.current_session_index = 0
        self.report_reasons = {
            'spam': InputReportReasonSpam(),
            'violence': InputReportReasonViolence(),
            'copyright': InputReportReasonCopyright(),
            'child_abuse': InputReportReasonChildAbuse(),
            'pornography': InputReportReasonPornography(),
            'fake': InputReportReasonFake(),
            'other': InputReportReasonOther()
        }
        self.report_count = 0
        self.successful_reports = 0
        self.failed_reports = 0
        
    async def initialize_sessions(self):
        """Initialize all available session files"""
        if not os.path.exists(self.sessions_dir):
            os.makedirs(self.sessions_dir)
            logger.warning(f"Created sessions directory: {self.sessions_dir}")
            logger.info("Please add .session files to the sessions directory")
            return
        
        session_files = [f for f in os.listdir(self.sessions_dir) if f.endswith('.session')]
        
        if not session_files:
            logger.error("No session files found in sessions directory")
            return
        
        logger.info(f"Found {len(session_files)} session files")
        
        for session_file in session_files:
            session_path = os.path.join(self.sessions_dir, session_file.replace('.session', ''))
            try:
                client = TelegramClient(session_path, self.api_id, self.api_hash)
                await client.connect()
                
                if await client.is_user_authorized():
                    self.clients.append(client)
                    me = await client.get_me()
                    logger.info(f"Session initialized: {session_file} -> @{me.username or me.first_name}")
                else:
                    logger.warning(f"Session {session_file} not authorized")
                    await client.disconnect()
                    
            except Exception as e:
                logger.error(f"Failed to initialize session {session_file}: {str(e)}")
        
        logger.info(f"Successfully initialized {len(self.clients)} sessions")
    
    def get_next_client(self) -> Optional[TelegramClient]:
        """Get next client in rotation"""
        if not self.clients:
            return None
        
        client = self.clients[self.current_session_index]
        self.current_session_index = (self.current_session_index + 1) % len(self.clients)
        return client
    
    async def send_report(self, channel_username: str, msg_id: int, category: str, 
                         comment: str = "") -> Dict[str, Any]:
        """
        Send a single report using session rotation
        
        Args:
            channel_username: Target channel username
            msg_id: Message ID to report
            category: Report category (spam, violence, copyright, etc.)
            comment: Optional comment for the report
            
        Returns:
            Dict with report results
        """
        client = self.get_next_client()
        if not client:
            return {
                'success': False,
                'error': 'No available sessions',
                'msg_id': msg_id,
                'category': category
            }
        
        if category not in self.report_reasons:
            return {
                'success': False,
                'error': f'Invalid category: {category}',
                'msg_id': msg_id,
                'category': category
            }
        
        self.report_count += 1
        
        try:
            # Get channel entity
            channel = await client.get_entity(channel_username)
            
            # Prepare report request
            report_reason = self.report_reasons[category]
            
            # Send report
            result = await client(ReportRequest(
                peer=channel,
                id=[msg_id],
                reason=report_reason,
                message=comment
            ))
            
            self.successful_reports += 1
            
            # Get session info
            me = await client.get_me()
            session_info = f"@{me.username}" if me.username else me.first_name
            
            logger.info(f"Report sent successfully - Session: {session_info}, "
                       f"Channel: {channel_username}, Msg: {msg_id}, Category: {category}")
            
            return {
                'success': True,
                'msg_id': msg_id,
                'category': category,
                'session': session_info,
                'result': str(result),
                'timestamp': time.time()
            }
            
        except Exception as e:
            self.failed_reports += 1
            error_msg = str(e)
            logger.error(f"Report failed - Channel: {channel_username}, "
                        f"Msg: {msg_id}, Category: {category}, Error: {error_msg}")
            
            return {
                'success': False,
                'msg_id': msg_id,
                'category': category,
                'error': error_msg,
                'timestamp': time.time()
            }
    
    async def send_batch_reports(self, channel_username: str, 
                                 reports_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send multiple reports with session rotation
        
        Args:
            channel_username: Target channel username
            reports_data: List of dicts with 'msg_id' and 'category' keys
            
        Returns:
            Dict with batch results
        """
        results = {
            'channel': channel_username,
            'total_reports': len(reports_data),
            'successful_reports': 0,
            'failed_reports': 0,
            'reports': []
        }
        
        logger.info(f"Starting batch report: {len(reports_data)} reports for {channel_username}")
        
        for i, report_data in enumerate(reports_data):
            msg_id = report_data['msg_id']
            category = report_data['category']
            comment = report_data.get('comment', '')
            
            # Send single report
            result = await self.send_report(channel_username, msg_id, category, comment)
            results['reports'].append(result)
            
            if result['success']:
                results['successful_reports'] += 1
            else:
                results['failed_reports'] += 1
            
            # Add random delay between reports (30-300 seconds)
            if i < len(reports_data) - 1:  # Don't delay after last report
                delay = random.uniform(30, 300)
                logger.info(f"Waiting {delay:.1f} seconds before next report...")
                await asyncio.sleep(delay)
        
        success_rate = (results['successful_reports'] / results['total_reports']) * 100
        logger.info(f"Batch report completed: {results['successful_reports']}/{results['total_reports']} "
                   f"successful ({success_rate:.1f}%)")
        
        return results
    
    async def send_reports_from_analysis(self, channel_username: str, 
                                       analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert analysis results to reports and send them
        
        Args:
            channel_username: Target channel username
            analysis_results: Results from violation analyzer
            
        Returns:
            Dict with reporting results
        """
        reports_data = []
        
        # Convert violations to report data
        for category, violations in analysis_results.get('violations', {}).items():
            if category in self.report_reasons:
                # Extract unique message IDs
                unique_msg_ids = list(set(v['message_id'] for v in violations))
                
                for msg_id in unique_msg_ids:
                    reports_data.append({
                        'msg_id': msg_id,
                        'category': category,
                        'comment': f"Automated compliance report: {category} violation detected"
                    })
        
        if not reports_data:
            logger.info("No violations found to report")
            return {
                'channel': channel_username,
                'total_reports': 0,
                'message': 'No violations found to report'
            }
        
        logger.info(f"Converted {len(reports_data)} violations to reports")
        return await self.send_batch_reports(channel_username, reports_data)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current reporting statistics"""
        return {
            'total_reports': self.report_count,
            'successful_reports': self.successful_reports,
            'failed_reports': self.failed_reports,
            'success_rate': (self.successful_reports / max(self.report_count, 1)) * 100,
            'active_sessions': len(self.clients),
            'current_session_index': self.current_session_index
        }
    
    async def cleanup(self):
        """Cleanup all client connections"""
        for client in self.clients:
            try:
                await client.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting client: {str(e)}")
        
        self.clients.clear()
        logger.info("All sessions cleaned up")

# Utility function for quick usage
async def quick_report(api_id: int, api_hash: str, channel: str, 
                      msg_id: int, category: str) -> Dict[str, Any]:
    """Quick single report function"""
    distributor = ComplianceReportDistributor(api_id, api_hash)
    await distributor.initialize_sessions()
    
    try:
        result = await distributor.send_report(channel, msg_id, category)
        return result
    finally:
        await distributor.cleanup()

# Example usage
async def main_example():
    """Example usage of the compliance report distributor"""
    # Configuration
    API_ID = 12345678  # Replace with your API ID
    API_HASH = "your_api_hash_here"  # Replace with your API hash
    
    # Initialize distributor
    distributor = ComplianceReportDistributor(API_ID, API_HASH)
    await distributor.initialize_sessions()
    
    try:
        # Example single report
        result = await distributor.send_report("@test_channel", 123, "spam")
        print(f"Single report result: {result}")
        
        # Example batch reports
        reports_data = [
            {'msg_id': 124, 'category': 'copyright'},
            {'msg_id': 125, 'category': 'violence'},
            {'msg_id': 126, 'category': 'spam'}
        ]
        
        batch_result = await distributor.send_batch_reports("@test_channel", reports_data)
        print(f"Batch report result: {batch_result}")
        
        # Print statistics
        stats = distributor.get_statistics()
        print(f"Statistics: {stats}")
        
    finally:
        await distributor.cleanup()

if __name__ == "__main__":
    asyncio.run(main_example())
