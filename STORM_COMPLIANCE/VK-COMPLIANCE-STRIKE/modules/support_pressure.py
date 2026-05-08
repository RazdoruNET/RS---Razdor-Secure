#!/usr/bin/env python3
"""
SUPPORT-PRESSURE Module
VK DMCA Claim Generation and Support Pressure System

This module handles:
- Automated DMCA claim generation
- Legal document preparation
- Support ticket submission
- Brand protection claims
"""

import requests
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
from jinja2 import Template
import hashlib
import base64

@dataclass
class DMCAClaim:
    """Data class for DMCA claim information"""
    original_content_url: str
    infringing_post_url: str
    copyright_holder: str
    brand_name: str
    content_description: str
    evidence_urls: List[str]
    contact_email: str
    physical_address: str
    signature: str
    claim_id: str = None

@dataclass
class SupportTicket:
    """Data class for support ticket"""
    ticket_id: str = None
    subject: str
    content: str
    category: str
    attachments: List[str]
    priority: str
    status: str = "pending"

class SupportPressure:
    """Main class for VK support pressure and DMCA claims"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.session = requests.Session()
        self.claims = []
        self.tickets = []
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file"""
        default_config = {
            "vk": {
                "support_url": "https://vk.com/support",
                "dmca_url": "https://vk.com/dmca",
                "api_endpoint": "https://api.vk.com/method/"
            },
            "legal": {
                "default_copyright_holders": [
                    "BMW AG",
                    "Mercedes-Benz Group AG",
                    "Audi AG",
                    "Porsche Automobil Holding SE"
                ],
                "template_dir": "./templates",
                "signature_line": "Authorized Agent for Copyright Holder"
            },
            "automation": {
                "batch_size": 10,
                "delay_between_claims": 300,  # 5 minutes
                "max_daily_claims": 100
            },
            "storage": {
                "claims_dir": "./data/dmca_claims",
                "tickets_dir": "./data/support_tickets",
                "templates_dir": "./templates"
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("SupportPressure")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler(
                Path("./data/logs") / "support_pressure.log",
                encoding='utf-8'
            )
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _generate_claim_id(self) -> str:
        """Generate unique claim ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_obj = hashlib.md5(f"{timestamp}_{len(self.claims)}".encode())
        return f"DMCA_{hash_obj.hexdigest()[:12].upper()}"
    
    def _load_template(self, template_name: str) -> Template:
        """Load Jinja2 template"""
        template_path = Path(self.config["legal"]["template_dir"]) / template_name
        
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
        else:
            # Use default template
            template_content = self._get_default_template(template_name)
        
        return Template(template_content)
    
    def _get_default_template(self, template_name: str) -> str:
        """Get default template content"""
        templates = {
            "dmca_claim.html": """
<!DOCTYPE html>
<html>
<head>
    <title>DMCA Takedown Notice</title>
</head>
<body>
    <h2>DMCA Takedown Notice</h2>
    <p><strong>Date:</strong> {{ date }}</p>
    <p><strong>Reference ID:</strong> {{ claim_id }}</p>
    
    <h3>Copyright Holder Information</h3>
    <p><strong>Company:</strong> {{ copyright_holder }}</p>
    <p><strong>Brand:</strong> {{ brand_name }}</p>
    <p><strong>Contact Email:</strong> {{ contact_email }}</p>
    <p><strong>Physical Address:</strong> {{ physical_address }}</p>
    
    <h3>Infringing Content</h3>
    <p><strong>Original Content URL:</strong> {{ original_content_url }}</p>
    <p><strong>Infringing Post URL:</strong> {{ infringing_post_url }}</p>
    <p><strong>Description:</strong> {{ content_description }}</p>
    
    <h3>Statement of Good Faith</h3>
    <p>I hereby state that I have a good faith belief that the disputed use of the copyrighted material is not authorized by the copyright owner, its agent, or the law.</p>
    
    <p>I hereby state that the information in this notification is accurate, and under penalty of perjury, that I am the owner, or an agent authorized to act on behalf of the owner, of an exclusive right that is allegedly infringed.</p>
    
    <h3>Electronic Signature</h3>
    <p>{{ signature }}</p>
    <p>{{ signature_line }}</p>
</body>
</html>
            """,
            
            "support_ticket.txt": """
Subject: {{ subject }}
Category: {{ category }}
Priority: {{ priority }}

Dear VK Support Team,

{{ content }}

Evidence URLs:
{% for url in evidence_urls %}
- {{ url }}
{% endfor %}

Contact Information:
Email: {{ contact_email }}
Company: {{ copyright_holder }}

Best regards,
{{ signature }}
{{ signature_line }}

---
Ticket ID: {{ ticket_id }}
Date: {{ date }}
            """
        }
        
        return templates.get(template_name, "")
    
    def create_dmca_claim(self, 
                         original_content_url: str,
                         infringing_post_url: str,
                         copyright_holder: str,
                         brand_name: str,
                         content_description: str,
                         evidence_urls: List[str],
                         contact_email: str,
                         physical_address: str,
                         signature: str) -> DMCAClaim:
        """Create a DMCA claim"""
        
        claim = DMCAClaim(
            original_content_url=original_content_url,
            infringing_post_url=infringing_post_url,
            copyright_holder=copyright_holder,
            brand_name=brand_name,
            content_description=content_description,
            evidence_urls=evidence_urls,
            contact_email=contact_email,
            physical_address=physical_address,
            signature=signature,
            claim_id=self._generate_claim_id()
        )
        
        self.claims.append(claim)
        self.logger.info(f"Created DMCA claim {claim.claim_id} for {infringing_post_url}")
        
        return claim
    
    def generate_dmca_document(self, claim: DMCAClaim) -> str:
        """Generate DMCA claim document"""
        template = self._load_template("dmca_claim.html")
        
        document = template.render(
            date=datetime.now().strftime("%Y-%m-%d"),
            claim_id=claim.claim_id,
            copyright_holder=claim.copyright_holder,
            brand_name=claim.brand_name,
            contact_email=claim.contact_email,
            physical_address=claim.physical_address,
            original_content_url=claim.original_content_url,
            infringing_post_url=claim.infringing_post_url,
            content_description=claim.content_description,
            signature=claim.signature,
            signature_line=self.config["legal"]["signature_line"]
        )
        
        return document
    
    def create_support_ticket(self,
                            subject: str,
                            content: str,
                            category: str = "copyright",
                            attachments: List[str] = None,
                            priority: str = "high",
                            contact_email: str = "",
                            copyright_holder: str = "") -> SupportTicket:
        """Create a support ticket"""
        
        ticket = SupportTicket(
            ticket_id=self._generate_claim_id().replace("DMCA_", "TICKET_"),
            subject=subject,
            content=content,
            category=category,
            attachments=attachments or [],
            priority=priority
        )
        
        self.tickets.append(ticket)
        self.logger.info(f"Created support ticket {ticket.ticket_id}")
        
        return ticket
    
    def generate_support_ticket_content(self, ticket: SupportTicket, claim: DMCAClaim = None) -> str:
        """Generate support ticket content"""
        template = self._load_template("support_ticket.txt")
        
        content = template.render(
            subject=ticket.subject,
            category=ticket.category,
            priority=ticket.priority,
            content=ticket.content,
            evidence_urls=claim.evidence_urls if claim else [],
            contact_email=claim.contact_email if claim else "",
            copyright_holder=claim.copyright_holder if claim else "",
            signature=claim.signature if claim else "Legal Representative",
            signature_line=self.config["legal"]["signature_line"],
            ticket_id=ticket.ticket_id,
            date=datetime.now().strftime("%Y-%m-%d")
        )
        
        return content
    
    def submit_dmca_claim(self, claim: DMCAClaim) -> bool:
        """Submit DMCA claim to VK"""
        try:
            # Generate DMCA document
            document = self.generate_dmca_document(claim)
            
            # Save document
            claims_dir = Path(self.config["storage"]["claims_dir"])
            claims_dir.mkdir(parents=True, exist_ok=True)
            
            document_path = claims_dir / f"{claim.claim_id}.html"
            with open(document_path, 'w', encoding='utf-8') as f:
                f.write(document)
            
            # Prepare form data for submission
            form_data = {
                'act': 'copyright',
                'url': claim.infringing_post_url,
                'original_url': claim.original_content_url,
                'description': claim.content_description,
                'copyright_holder': claim.copyright_holder,
                'contact_email': claim.contact_email,
                'physical_address': claim.physical_address,
                'signature': claim.signature
            }
            
            # Submit to VK DMCA endpoint
            response = self.session.post(
                self.config["vk"]["dmca_url"],
                data=form_data,
                timeout=30
            )
            
            if response.status_code == 200:
                self.logger.info(f"DMCA claim {claim.claim_id} submitted successfully")
                return True
            else:
                self.logger.error(f"DMCA claim submission failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error submitting DMCA claim {claim.claim_id}: {e}")
            return False
    
    def submit_support_ticket(self, ticket: SupportTicket) -> bool:
        """Submit support ticket to VK"""
        try:
            # Generate ticket content
            content = self.generate_support_ticket_content(ticket)
            
            # Save ticket
            tickets_dir = Path(self.config["storage"]["tickets_dir"])
            tickets_dir.mkdir(parents=True, exist_ok=True)
            
            ticket_path = tickets_dir / f"{ticket.ticket_id}.txt"
            with open(ticket_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Prepare form data
            form_data = {
                'act': 'support',
                'subject': ticket.subject,
                'question': content,
                'category': ticket.category,
                'priority': ticket.priority
            }
            
            # Submit to VK support endpoint
            response = self.session.post(
                self.config["vk"]["support_url"],
                data=form_data,
                timeout=30
            )
            
            if response.status_code == 200:
                self.logger.info(f"Support ticket {ticket.ticket_id} submitted successfully")
                return True
            else:
                self.logger.error(f"Support ticket submission failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error submitting support ticket {ticket.ticket_id}: {e}")
            return False
    
    def batch_submit_claims(self, claims: List[DMCAClaim]) -> Dict:
        """Submit multiple DMCA claims with rate limiting"""
        results = {
            "total": len(claims),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for i, claim in enumerate(claims):
            try:
                success = self.submit_dmca_claim(claim)
                if success:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                
                # Rate limiting
                if i < len(claims) - 1:  # Don't delay after last claim
                    time.sleep(self.config["automation"]["delay_between_claims"])
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(str(e))
                self.logger.error(f"Batch claim error: {e}")
        
        self.logger.info(f"Batch DMCA claims completed: {results['successful']}/{results['total']} successful")
        return results
    
    def generate_brand_protection_claims(self, violations: List[Dict]) -> List[DMCAClaim]:
        """Generate DMCA claims for brand protection"""
        claims = []
        
        for violation in violations:
            # Map violation to brand
            brand_mapping = {
                "bmw": "BMW AG",
                "mercedes": "Mercedes-Benz Group AG",
                "audi": "Audi AG",
                "porsche": "Porsche Automobil Holding SE"
            }
            
            # Extract brand from violation
            content_text = violation.get("evidence", {}).get("text_snippet", "").lower()
            detected_brand = None
            
            for brand_key, brand_name in brand_mapping.items():
                if brand_key in content_text:
                    detected_brand = brand_name
                    break
            
            if not detected_brand:
                detected_brand = self.config["legal"]["default_copyright_holders"][0]
            
            claim = self.create_dmca_claim(
                original_content_url=f"https://example.com/original/{detected_brand.lower().replace(' ', '_')}",
                infringing_post_url=violation.get("post_url", ""),
                copyright_holder=detected_brand,
                brand_name=detected_brand,
                content_description=violation.get("evidence", {}).get("text_snippet", ""),
                evidence_urls=[violation.get("post_url", "")],
                contact_email=f"legal@{detected_brand.lower().replace(' ', '')}.com",
                physical_address=f"{detected_brand} Headquarters, Germany",
                signature=f"Legal Representative, {detected_brand}"
            )
            
            claims.append(claim)
        
        return claims
    
    def get_submission_summary(self) -> Dict:
        """Get summary of all submissions"""
        return {
            "total_dmca_claims": len(self.claims),
            "total_support_tickets": len(self.tickets),
            "claims_by_brand": {
                claim.brand_name: len([c for c in self.claims if c.brand_name == claim.brand_name])
                for claim in self.claims
            },
            "tickets_by_category": {
                ticket.category: len([t for t in self.tickets if t.category == ticket.category])
                for ticket in self.tickets
            }
        }

if __name__ == "__main__":
    # Example usage
    pressure = SupportPressure()
    
    # Create sample DMCA claim
    claim = pressure.create_dmca_claim(
        original_content_url="https://example.com/original/bmw_video",
        infringing_post_url="https://vk.com/wall-123456789_123456789",
        copyright_holder="BMW AG",
        brand_name="BMW",
        content_description="Unauthorized use of BMW promotional video",
        evidence_urls=["https://vk.com/wall-123456789_123456789"],
        contact_email="legal@bmw.com",
        physical_address="BMW Headquarters, Munich, Germany",
        signature="Legal Representative, BMW AG"
    )
    
    # Submit claim
    success = pressure.submit_dmca_claim(claim)
    print(f"DMCA claim submission: {'Success' if success else 'Failed'}")
    
    # Get summary
    summary = pressure.get_submission_summary()
    print(f"Submission summary: {summary}")
