import asyncio
import logging
import random
import json
from typing import List, Dict, Any
from telethon import TelegramClient
from telethon.tl.functions.messages import ReportRequest
from telethon.tl.types import InputPeerChannel, InputPeerUser
from datetime import datetime, timedelta
from asyncio_throttle import Throttler

logger = logging.getLogger(__name__)

class ComplianceReporter:
    def __init__(self, api_id: str, api_hash: str, session_files: List[str]):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_files = session_files
        self.clients = []
        self.throttler = Throttler(rate_limit=1, period=30)  # 1 report per 30 seconds per client
        self.report_history = []
    
    async def initialize_clients(self):
        """Initialize multiple Telegram clients for distributed reporting"""
        for session_file in self.session_files:
            try:
                client = TelegramClient(f'sessions/{session_file}', self.api_id, self.api_hash)
                await client.connect()
                if await client.is_user_authorized():
                    self.clients.append(client)
                    logger.info(f"Client {session_file} initialized successfully")
                else:
                    logger.warning(f"Client {session_file} not authorized")
            except Exception as e:
                logger.error(f"Failed to initialize client {session_file}: {str(e)}")
    
    async def submit_compliance_report(self, channel_username: str, message_ids: List[int], 
                                     report_reason: str, comment: str = "") -> Dict[str, Any]:
        """Submit compliance report using distributed clients"""
        results = {
            'channel': channel_username,
            'message_ids': message_ids,
            'report_reason': report_reason,
            'successful_reports': 0,
            'failed_reports': 0,
            'details': []
        }
        
        if not self.clients:
            await self.initialize_clients()
        
        if not self.clients:
            raise Exception("No authorized clients available for reporting")
        
        # Distribute reports across available clients
        client_index = 0
        for msg_id in message_ids:
            client = self.clients[client_index % len(self.clients)]
            client_index += 1
            
            try:
                async with self.throttler:
                    report_result = await self._submit_single_report(client, channel_username, msg_id, report_reason, comment)
                    results['successful_reports'] += 1
                    results['details'].append(report_result)
                    
                    # Add jitter to avoid detection
                    await asyncio.sleep(random.uniform(30, 300))
                    
            except Exception as e:
                results['failed_reports'] += 1
                results['details'].append({
                    'message_id': msg_id,
                    'status': 'failed',
                    'error': str(e)
                })
                logger.error(f"Failed to report message {msg_id}: {str(e)}")
        
        # Record report in history
        self.report_history.append({
            'timestamp': datetime.now().isoformat(),
            'channel': channel_username,
            'message_count': len(message_ids),
            'reason': report_reason,
            'success_rate': results['successful_reports'] / len(message_ids)
        })
        
        return results
    
    async def _submit_single_report(self, client: TelegramClient, channel_username: str, 
                                   message_id: int, reason: str, comment: str) -> Dict[str, Any]:
        """Submit a single report using specified client"""
        try:
            # Get the channel entity
            channel = await client.get_entity(channel_username)
            
            # Submit report
            result = await client(ReportRequest(
                peer=channel,
                id=[message_id],
                reason=self._get_report_reason_code(reason),
                message=comment
            ))
            
            return {
                'message_id': message_id,
                'status': 'success',
                'client': client.session.filename,
                'timestamp': datetime.now().isoformat(),
                'result': str(result)
            }
            
        except Exception as e:
            raise Exception(f"Report submission failed: {str(e)}")
    
    def _get_report_reason_code(self, reason: str) -> int:
        """Convert reason string to Telegram report reason code"""
        reason_codes = {
            'spam': 0,
            'violence': 1,
            'pornography': 2,
            'child_abuse': 3,
            'copyright': 4,
            'fake': 5,
            'other': 6
        }
        return reason_codes.get(reason.lower(), 6)  # Default to 'other'
    
    async def batch_report_violations(self, violations_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit batch reports for multiple violation types"""
        batch_results = {
            'channel': violations_data['channel'],
            'total_reports': 0,
            'successful_reports': 0,
            'failed_reports': 0,
            'category_results': {}
        }
        
        for category, violations in violations_data['violations'].items():
            if not violations:
                continue
            
            # Extract message IDs from violations
            message_ids = list(set([v['message_id'] for v in violations]))
            
            # Submit reports for this category
            try:
                result = await self.submit_compliance_report(
                    violations_data['channel'],
                    message_ids,
                    category,
                    f"Automated compliance report: {len(message_ids)} violations detected"
                )
                
                batch_results['category_results'][category] = result
                batch_results['total_reports'] += len(message_ids)
                batch_results['successful_reports'] += result['successful_reports']
                batch_results['failed_reports'] += result['failed_reports']
                
                # Wait between categories to avoid rate limiting
                await asyncio.sleep(random.uniform(300, 600))
                
            except Exception as e:
                logger.error(f"Failed to submit batch reports for {category}: {str(e)}")
                batch_results['category_results'][category] = {
                    'error': str(e),
                    'message_ids': message_ids
                }
        
        return batch_results
    
    async def get_report_statistics(self) -> Dict[str, Any]:
        """Get statistics about submitted reports"""
        if not self.report_history:
            return {'message': 'No reports submitted yet'}
        
        total_reports = sum(r['message_count'] for r in self.report_history)
        avg_success_rate = sum(r['success_rate'] for r in self.report_history) / len(self.report_history)
        
        recent_reports = [r for r in self.report_history 
                         if datetime.fromisoformat(r['timestamp']) > datetime.now() - timedelta(days=7)]
        
        return {
            'total_reports_submitted': total_reports,
            'average_success_rate': avg_success_rate,
            'reports_last_7_days': len(recent_reports),
            'active_clients': len(self.clients),
            'last_report_time': self.report_history[-1]['timestamp'] if self.report_history else None
        }
    
    async def cleanup(self):
        """Clean up client connections"""
        for client in self.clients:
            try:
                await client.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting client: {str(e)}")
        self.clients.clear()
