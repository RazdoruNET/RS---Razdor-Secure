import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any
from datetime import datetime
import os
from jinja2 import Template
import json

logger = logging.getLogger(__name__)

class DMCAEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.smtp_server = config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = config.get('smtp_port', 587)
        self.sender_email = config.get('sender_email')
        self.sender_password = config.get('sender_password')
        self.template_dir = config.get('template_dir', 'templates')
        
    def load_template(self, template_name: str) -> Template:
        """Load email template from file"""
        template_path = os.path.join(self.template_dir, template_name)
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            return Template(template_content)
        except FileNotFoundError:
            logger.error(f"Template {template_name} not found, using default")
            return self._get_default_template()
    
    def _get_default_template(self) -> Template:
        """Get default DMCA notice template"""
        template_content = """
        DMCA NOTICE OF COPYRIGHT INFRINGEMENT
        
        Date: {{ date }}
        
        To: {{ recipient }}
        From: {{ sender_name }} ({{ sender_email }})
        Company: {{ company_name }}
        Address: {{ sender_address }}
        Phone: {{ sender_phone }}
        
        RE: NOTICE OF COPYRIGHT INFRINGEMENT - Case #{{ case_number }}
        
        Dear Telegram Support Team,
        
        I am writing to notify you of copyright infringement occurring on your platform. 
        Under penalty of perjury, I state that I am the copyright owner or authorized 
        to act on behalf of the copyright owner of the exclusive rights that are being infringed.
        
        IDENTIFIED INFRINGING CONTENT:
        {% for item in infringing_items %}
        - Channel: {{ item.channel }}
        - Message ID: {{ item.message_id }}
        - Content Type: {{ item.content_type }}
        - Description: {{ item.description }}
        - Direct Link: {{ item.direct_link }}
        {% endfor %}
        
        ORIGINAL COPYRIGHTED WORK:
        - Title: {{ original_work.title }}
        - Author/Artist: {{ original_work.author }}
        - Registration Number: {{ original_work.registration_number }}
        - Publication Date: {{ original_work.publication_date }}
        
        VIOLATION DETAILS:
        The infringing content posted on your platform reproduces, distributes, and displays 
        our copyrighted work without authorization. This constitutes direct copyright infringement 
        under 17 U.S.C. § 106 and international copyright treaties.
        
        GOOD FAITH BELIEF STATEMENT:
        I have a good faith belief that the use of the copyrighted materials described above 
        is not authorized by the copyright owner, its agent, or the law.
        
        ACCURACY STATEMENT:
        I swear, under penalty of perjury, that the information in this notification is accurate 
        and that I am the copyright owner or am authorized to act on behalf of the owner of an 
        exclusive right that is allegedly infringed.
        
        ELECTRONIC SIGNATURE:
        {{ digital_signature }}
        
        DEMAND FOR ACTION:
        We request that you:
        1. Immediately remove or disable access to the infringing content
        2. Notify the user responsible for the infringement of this action
        3. Take appropriate measures to prevent future infringement by this user
        
        Please respond within 24-48 hours to confirm receipt of this notice and the actions taken.
        
        Sincerely,
        
        {{ sender_name }}
        {{ company_name }}
        {{ sender_title }}
        {{ sender_email }}
        {{ sender_phone }}
        
        ---
        This DMCA notice is sent in accordance with the Digital Millennium Copyright Act (17 U.S.C. § 512)
        and applicable international copyright laws.
        """
        return Template(template_content)
    
    def generate_dmca_notice(self, case_data: Dict[str, Any]) -> str:
        """Generate DMCA notice content"""
        template = self.load_template('dmca_notice.html')
        
        # Add default values if not provided
        case_data.setdefault('date', datetime.now().strftime('%B %d, %Y'))
        case_data.setdefault('case_number', f"DMCA-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        case_data.setdefault('recipient', 'dmca@telegram.org')
        
        return template.render(**case_data)
    
    def create_case_data(self, violations: List[Dict[str, Any]], copyright_info: Dict[str, Any], 
                        sender_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create structured case data for DMCA notice"""
        case_data = {
            'infringing_items': [],
            'original_work': copyright_info,
            'sender_name': sender_info.get('name'),
            'sender_email': sender_info.get('email'),
            'sender_title': sender_info.get('title', 'Copyright Agent'),
            'company_name': sender_info.get('company'),
            'sender_address': sender_info.get('address'),
            'sender_phone': sender_info.get('phone'),
            'digital_signature': f"/s/ {sender_info.get('name', 'Authorized Agent')}"
        }
        
        # Process violations
        for violation in violations:
            item = {
                'channel': violation.get('channel'),
                'message_id': violation.get('message_id'),
                'content_type': violation.get('media_type', 'text'),
                'description': violation.get('text', '')[:200],
                'direct_link': f"https://t.me/{violation.get('channel')}/{violation.get('message_id')}"
            }
            case_data['infringing_items'].append(item)
        
        return case_data
    
    async def send_dmca_notice(self, recipient_email: str, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send DMCA notice via email"""
        result = {
            'success': False,
            'case_number': case_data.get('case_number'),
            'recipient': recipient_email,
            'timestamp': datetime.now().isoformat(),
            'error': None
        }
        
        try:
            # Generate notice content
            notice_content = self.generate_dmca_notice(case_data)
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f"DMCA Takedown Notice - Case #{case_data.get('case_number')}"
            
            # Attach the notice
            msg.attach(MIMEText(notice_content, 'plain'))
            
            # Add evidence attachments if provided
            if 'evidence_files' in case_data:
                for file_path in case_data['evidence_files']:
                    if os.path.exists(file_path):
                        self._attach_file(msg, file_path)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            
            text = msg.as_string()
            server.sendmail(self.sender_email, recipient_email, text)
            server.quit()
            
            result['success'] = True
            logger.info(f"DMCA notice sent successfully to {recipient_email}")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Failed to send DMCA notice: {str(e)}")
        
        return result
    
    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """Attach file to email"""
        try:
            with open(file_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(file_path)}'
            )
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"Failed to attach file {file_path}: {str(e)}")
    
    def batch_generate_notices(self, violation_groups: Dict[str, List[Dict[str, Any]]], 
                             copyright_info: Dict[str, Any], sender_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate batch DMCA notices for multiple violation groups"""
        notices = []
        
        for channel, violations in violation_groups.items():
            if not violations:
                continue
            
            case_data = self.create_case_data(violations, copyright_info, sender_info)
            notice_content = self.generate_dmca_notice(case_data)
            
            notice = {
                'channel': channel,
                'case_number': case_data['case_number'],
                'violation_count': len(violations),
                'notice_content': notice_content,
                'generated_at': datetime.now().isoformat()
            }
            
            notices.append(notice)
        
        return notices
    
    async def send_batch_notices(self, notices: List[Dict[str, Any]], 
                               recipient_email: str = 'dmca@telegram.org') -> List[Dict[str, Any]]:
        """Send batch DMCA notices"""
        results = []
        
        for notice in notices:
            try:
                # Parse notice content back to case data
                case_data = {
                    'case_number': notice['case_number'],
                    'infringing_items': [],  # Would need to parse from notice_content
                    'original_work': {},
                    'sender_name': 'Copyright Agent',
                    'sender_email': self.sender_email,
                    'digital_signature': '/s/ Authorized Agent'
                }
                
                result = await self.send_dmca_notice(recipient_email, case_data)
                results.append(result)
                
                # Add delay between sends to avoid rate limiting
                await asyncio.sleep(60)
                
            except Exception as e:
                results.append({
                    'success': False,
                    'case_number': notice.get('case_number'),
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        return results
    
    def create_evidence_package(self, violations: List[Dict[str, Any]], output_dir: str = 'evidence') -> str:
        """Create evidence package for DMCA case"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Create evidence summary
        evidence_data = {
            'case_number': f"EVIDENCE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'created_at': datetime.now().isoformat(),
            'total_violations': len(violations),
            'violations': violations
        }
        
        # Save evidence summary
        evidence_file = os.path.join(output_dir, f"evidence_{evidence_data['case_number']}.json")
        with open(evidence_file, 'w', encoding='utf-8') as f:
            json.dump(evidence_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Evidence package created: {evidence_file}")
        return evidence_file
    
    def get_dmca_statistics(self) -> Dict[str, Any]:
        """Get statistics about DMCA notices sent"""
        # This would typically read from a database
        return {
            'total_notices_sent': 0,
            'successful_takedowns': 0,
            'pending_cases': 0,
            'average_response_time_hours': 0,
            'last_notice_date': None
        }

import asyncio
