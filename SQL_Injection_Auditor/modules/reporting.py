#!/usr/bin/env python3
"""
Reporting Module
Generates comprehensive security audit reports in JSON and PDF formats
"""

import json
import datetime
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging
from pathlib import Path

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("ReportLab not available. PDF reports will be disabled.")

from modules.analysis_engine import Vulnerability, InjectionType, DatabaseType
from modules.verification import VerificationResult, VerificationStatus

@dataclass
class ScanSummary:
    """Summary of the security scan"""
    scan_date: str
    target_url: str
    total_vectors_tested: int
    vulnerabilities_found: int
    high_risk_vulnerabilities: int
    medium_risk_vulnerabilities: int
    low_risk_vulnerabilities: int
    scan_duration: float
    databases_detected: List[str]

@dataclass
class ReportData:
    """Complete report data structure"""
    summary: ScanSummary
    vulnerabilities: List[Dict[str, Any]]
    verification_results: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    technical_details: Dict[str, Any]

class VulnerabilityClassifier:
    """Classifies vulnerabilities by risk level"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def classify_vulnerability(self, vulnerability: Vulnerability, 
                             verification_result: Optional[VerificationResult] = None) -> Dict[str, Any]:
        """Classify vulnerability by risk level"""
        base_score = self._calculate_base_score(vulnerability)
        
        # Adjust score based on verification
        if verification_result:
            if verification_result.status == VerificationStatus.CONFIRMED:
                base_score += 2
            elif verification_result.status == VerificationStatus.LIKELY:
                base_score += 1
            elif verification_result.status == VerificationStatus.FALSE_POSITIVE:
                base_score -= 3
        
        # Determine risk level
        if base_score >= 8:
            risk_level = "HIGH"
            severity = "CRITICAL"
        elif base_score >= 6:
            risk_level = "HIGH"
            severity = "HIGH"
        elif base_score >= 4:
            risk_level = "MEDIUM"
            severity = "MEDIUM"
        else:
            risk_level = "LOW"
            severity = "LOW"
        
        return {
            'vulnerability': vulnerability,
            'risk_level': risk_level,
            'severity': severity,
            'cvss_score': min(10.0, base_score),
            'base_score': base_score,
            'verified': verification_result is not None,
            'verification_status': verification_result.status.value if verification_result else None
        }
    
    def _calculate_base_score(self, vulnerability: Vulnerability) -> float:
        """Calculate base vulnerability score"""
        score = 0.0
        
        # Injection type scoring
        injection_scores = {
            InjectionType.ERROR_BASED: 4.0,
            InjectionType.UNION_BASED: 4.5,
            InjectionType.BOOLEAN_BASED: 3.5,
            InjectionType.TIME_BASED: 3.0
        }
        score += injection_scores.get(vulnerability.injection_type, 2.0)
        
        # Database type scoring
        db_scores = {
            DatabaseType.MYSQL: 1.0,
            DatabaseType.POSTGRESQL: 1.0,
            DatabaseType.MSSQL: 1.2,
            DatabaseType.ORACLE: 1.3,
            DatabaseType.SQLITE: 0.8
        }
        score *= db_scores.get(vulnerability.database_type, 1.0)
        
        # Confidence scoring
        score += vulnerability.confidence * 2.0
        
        # Parameter risk scoring
        high_risk_params = ['id', 'user', 'username', 'password', 'email', 'admin']
        if any(risk in vulnerability.parameter.lower() for risk in high_risk_params):
            score += 1.5
        
        # URL pattern scoring
        if 'admin' in vulnerability.url.lower() or 'login' in vulnerability.url.lower():
            score += 1.0
        
        return min(score, 10.0)

class RecommendationEngine:
    """Generates remediation recommendations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.recommendations = self._load_recommendations()
    
    def _load_recommendations(self) -> Dict[str, Dict[str, Any]]:
        """Load vulnerability recommendations"""
        return {
            'general': {
                'title': 'General SQL Injection Prevention',
                'description': 'Implement comprehensive SQL injection prevention measures',
                'recommendations': [
                    'Use parameterized queries or prepared statements',
                    'Implement input validation and sanitization',
                    'Apply principle of least privilege to database accounts',
                    'Regularly update and patch database systems',
                    'Implement Web Application Firewall (WAF)',
                    'Conduct regular security audits and penetration testing'
                ],
                'code_examples': {
                    'php': '$stmt = $pdo->prepare("SELECT * FROM users WHERE id = ?"); $stmt->execute([$id]);',
                    'python': 'cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))',
                    'java': 'PreparedStatement stmt = conn.prepareStatement("SELECT * FROM users WHERE id = ?"); stmt.setInt(1, userId);',
                    'node': 'db.query("SELECT * FROM users WHERE id = ?", [userId]);'
                }
            },
            'parameterized_queries': {
                'title': 'Implement Parameterized Queries',
                'description': 'Replace dynamic SQL with parameterized queries',
                'recommendations': [
                    'Use PDO prepared statements in PHP',
                    'Use parameterized queries in Python (psycopg2, pymysql)',
                    'Use PreparedStatement in Java',
                    'Use parameter binding in Node.js',
                    'Never concatenate user input directly into SQL queries'
                ]
            },
            'input_validation': {
                'title': 'Input Validation and Sanitization',
                'description': 'Validate and sanitize all user inputs',
                'recommendations': [
                    'Validate input format and length',
                    'Sanitize special characters',
                    'Use whitelist approach for allowed characters',
                    'Implement server-side validation (client-side is not enough)',
                    'Reject suspicious input patterns'
                ]
            },
            'database_security': {
                'title': 'Database Security Hardening',
                'description': 'Harden database security configuration',
                'recommendations': [
                    'Use least privilege database accounts',
                    'Disable unnecessary database functions',
                    'Enable database auditing and logging',
                    'Regularly review database permissions',
                    'Separate development and production databases'
                ]
            }
        }
    
    def generate_recommendations(self, vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate specific recommendations based on vulnerabilities"""
        recommendations = []
        
        # Add general recommendations
        recommendations.append(self.recommendations['general'])
        
        # Add specific recommendations based on vulnerability types
        injection_types = set()
        for vuln in vulnerabilities:
            injection_types.add(vuln['vulnerability'].injection_type.value)
        
        if InjectionType.ERROR_BASED.value in injection_types:
            recommendations.append(self.recommendations['parameterized_queries'])
        
        if InjectionType.UNION_BASED.value in injection_types:
            recommendations.append(self.recommendations['input_validation'])
        
        # Add database-specific recommendations
        databases_detected = set()
        for vuln in vulnerabilities:
            databases_detected.add(vuln['vulnerability'].database_type.value)
        
        if databases_detected:
            recommendations.append(self.recommendations['database_security'])
        
        return recommendations

class JSONReporter:
    """Generates JSON format reports"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_report(self, report_data: ReportData, output_path: str) -> str:
        """Generate JSON report"""
        try:
            # Convert dataclasses to dictionaries
            report_dict = {
                'scan_summary': asdict(report_data.summary),
                'vulnerabilities': [],
                'verification_results': [],
                'recommendations': report_data.recommendations,
                'technical_details': report_data.technical_details,
                'report_metadata': {
                    'generated_at': datetime.datetime.now().isoformat(),
                    'generator': 'SQL Injection Auditor v1.0',
                    'format': 'JSON'
                }
            }
            
            # Convert vulnerabilities
            for vuln in report_data.vulnerabilities:
                if isinstance(vuln.get('vulnerability'), Vulnerability):
                    vuln_dict = asdict(vuln['vulnerability'])
                    vuln_dict.update({k: v for k, v in vuln.items() if k != 'vulnerability'})
                    report_dict['vulnerabilities'].append(vuln_dict)
                else:
                    report_dict['vulnerabilities'].append(vuln)
            
            # Convert verification results
            for vr in report_data.verification_results:
                if isinstance(vr, VerificationResult):
                    vr_dict = {
                        'vulnerability': asdict(vr.vulnerability),
                        'status': vr.status.value,
                        'confidence': vr.confidence,
                        'verification_tests': vr.verification_tests,
                        'evidence': vr.evidence,
                        'false_positive_indicators': vr.false_positive_indicators
                    }
                    report_dict['verification_results'].append(vr_dict)
                else:
                    report_dict['verification_results'].append(vr)
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"JSON report generated: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error generating JSON report: {e}")
            raise

class PDFReporter:
    """Generates PDF format reports"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation")
        
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomSubheading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            textColor=colors.darkgreen
        ))
    
    def generate_report(self, report_data: ReportData, output_path: str) -> str:
        """Generate PDF report"""
        try:
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            story = []
            
            # Title page
            self._add_title_page(story, report_data)
            
            # Executive summary
            self._add_executive_summary(story, report_data)
            
            # Vulnerabilities section
            self._add_vulnerabilities_section(story, report_data)
            
            # Verification results
            self._add_verification_section(story, report_data)
            
            # Recommendations
            self._add_recommendations_section(story, report_data)
            
            # Technical details
            self._add_technical_details_section(story, report_data)
            
            # Build PDF
            doc.build(story)
            
            self.logger.info(f"PDF report generated: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error generating PDF report: {e}")
            raise
    
    def _add_title_page(self, story: List, report_data: ReportData):
        """Add title page"""
        story.append(Paragraph("SQL INJECTION SECURITY AUDIT REPORT", self.styles['CustomTitle']))
        story.append(Spacer(1, 50))
        
        title_data = [
            ['Target URL:', report_data.summary.target_url],
            ['Scan Date:', report_data.summary.scan_date],
            ['Total Vectors Tested:', str(report_data.summary.total_vectors_tested)],
            ['Vulnerabilities Found:', str(report_data.summary.vulnerabilities_found)],
            ['High Risk:', str(report_data.summary.high_risk_vulnerabilities)],
            ['Medium Risk:', str(report_data.summary.medium_risk_vulnerabilities)],
            ['Low Risk:', str(report_data.summary.low_risk_vulnerabilities)],
            ['Scan Duration:', f"{report_data.summary.scan_duration:.2f} seconds"]
        ]
        
        table = Table(title_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ]))
        
        story.append(table)
        story.append(PageBreak())
    
    def _add_executive_summary(self, story: List, report_data: ReportData):
        """Add executive summary"""
        story.append(Paragraph("EXECUTIVE SUMMARY", self.styles['CustomHeading']))
        
        summary_text = f"""
        This report presents the findings of a comprehensive SQL injection security audit 
        conducted on {report_data.summary.target_url}. The scan identified {report_data.summary.vulnerabilities_found} 
        potential SQL injection vulnerabilities across {report_data.summary.total_vectors_tested} input vectors.
        """
        
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Risk breakdown
        risk_data = [
            ['Risk Level', 'Count', 'Percentage'],
            ['HIGH', str(report_data.summary.high_risk_vulnerabilities), 
             f"{(report_data.summary.high_risk_vulnerabilities/max(1,report_data.summary.vulnerabilities_found)*100):.1f}%"],
            ['MEDIUM', str(report_data.summary.medium_risk_vulnerabilities),
             f"{(report_data.summary.medium_risk_vulnerabilities/max(1,report_data.summary.vulnerabilities_found)*100):.1f}%"],
            ['LOW', str(report_data.summary.low_risk_vulnerabilities),
             f"{(report_data.summary.low_risk_vulnerabilities/max(1,report_data.summary.vulnerabilities_found)*100):.1f}%"]
        ]
        
        risk_table = Table(risk_data, colWidths=[2*inch, 1*inch, 1*inch])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(risk_table)
        story.append(Spacer(1, 20))
    
    def _add_vulnerabilities_section(self, story: List, report_data: ReportData):
        """Add vulnerabilities section"""
        story.append(Paragraph("VULNERABILITIES DETECTED", self.styles['CustomHeading']))
        
        if not report_data.vulnerabilities:
            story.append(Paragraph("No vulnerabilities were detected during the scan.", self.styles['Normal']))
            return
        
        for i, vuln_data in enumerate(report_data.vulnerabilities, 1):
            vuln = vuln_data['vulnerability']
            story.append(Paragraph(f"Vulnerability #{i}: {vuln_data['risk_level']}", self.styles['CustomSubheading']))
            
            vuln_info = [
                ['URL:', vuln.url],
                ['Parameter:', vuln.parameter],
                ['Injection Type:', vuln.injection_type.value],
                ['Database Type:', vuln.database_type.value],
                ['Risk Level:', vuln_data['risk_level']],
                ['CVSS Score:', f"{vuln_data['cvss_score']:.1f}"],
                ['Confidence:', f"{vuln.confidence:.2f}"]
            ]
            
            vuln_table = Table(vuln_info, colWidths=[1.5*inch, 4.5*inch])
            vuln_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(vuln_table)
            story.append(Spacer(1, 12))
            
            if vuln.error_message:
                story.append(Paragraph(f"Error Message: {vuln.error_message}", self.styles['Normal']))
                story.append(Spacer(1, 6))
            
            story.append(Paragraph(f"Payload Used: {vuln.payload}", self.styles['Code']))
            story.append(Spacer(1, 12))
    
    def _add_verification_section(self, story: List, report_data: ReportData):
        """Add verification results section"""
        story.append(Paragraph("VERIFICATION RESULTS", self.styles['CustomHeading']))
        
        if not report_data.verification_results:
            story.append(Paragraph("No verification results available.", self.styles['Normal']))
            return
        
        for vr in report_data.verification_results:
            story.append(Paragraph(f"Status: {vr.status.value.upper()}", self.styles['CustomSubheading']))
            story.append(Paragraph(f"Confidence: {vr.confidence:.2f}", self.styles['Normal']))
            
            if vr.evidence:
                story.append(Paragraph("Evidence:", self.styles['Normal']))
                for evidence in vr.evidence:
                    story.append(Paragraph(f"• {evidence}", self.styles['Normal']))
            
            story.append(Spacer(1, 12))
    
    def _add_recommendations_section(self, story: List, report_data: ReportData):
        """Add recommendations section"""
        story.append(Paragraph("RECOMMENDATIONS", self.styles['CustomHeading']))
        
        for rec in report_data.recommendations:
            story.append(Paragraph(rec['title'], self.styles['CustomSubheading']))
            story.append(Paragraph(rec['description'], self.styles['Normal']))
            
            for recommendation in rec['recommendations']:
                story.append(Paragraph(f"• {recommendation}", self.styles['Normal']))
            
            if 'code_examples' in rec:
                story.append(Paragraph("Code Examples:", self.styles['Normal']))
                for lang, code in rec['code_examples'].items():
                    story.append(Paragraph(f"{lang.upper()}:", self.styles['Normal']))
                    story.append(Paragraph(code, self.styles['Code']))
            
            story.append(Spacer(1, 12))
    
    def _add_technical_details_section(self, story: List, report_data: ReportData):
        """Add technical details section"""
        story.append(Paragraph("TECHNICAL DETAILS", self.styles['CustomHeading']))
        
        for key, value in report_data.technical_details.items():
            story.append(Paragraph(f"{key.replace('_', ' ').title()}:", self.styles['CustomSubheading']))
            if isinstance(value, list):
                for item in value:
                    story.append(Paragraph(f"• {item}", self.styles['Normal']))
            else:
                story.append(Paragraph(str(value), self.styles['Normal']))
            story.append(Spacer(1, 8))

class ReportGenerator:
    """Main report generation engine"""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        self.classifier = VulnerabilityClassifier()
        self.recommendation_engine = RecommendationEngine()
        self.json_reporter = JSONReporter()
        
        if REPORTLAB_AVAILABLE:
            self.pdf_reporter = PDFReporter()
        else:
            self.pdf_reporter = None
    
    def generate_report(self, vulnerabilities: List[Vulnerability], 
                       verification_results: List[VerificationResult] = None,
                       scan_summary: ScanSummary = None,
                       technical_details: Dict[str, Any] = None,
                       formats: List[str] = ['json']) -> List[str]:
        """Generate security audit report"""
        
        # Classify vulnerabilities
        classified_vulnerabilities = []
        for vuln in vulnerabilities:
            verification = None
            if verification_results:
                verification = next((vr for vr in verification_results if vr.vulnerability == vuln), None)
            
            classified = self.classifier.classify_vulnerability(vuln, verification)
            classified_vulnerabilities.append(classified)
        
        # Generate recommendations
        recommendations = self.recommendation_engine.generate_recommendations(classified_vulnerabilities)
        
        # Create report data
        report_data = ReportData(
            summary=scan_summary or self._create_default_summary(vulnerabilities),
            vulnerabilities=classified_vulnerabilities,
            verification_results=verification_results or [],
            recommendations=recommendations,
            technical_details=technical_details or {}
        )
        
        # Generate reports in requested formats
        generated_files = []
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if 'json' in formats:
            json_path = self.output_dir / f"sql_injection_report_{timestamp}.json"
            generated_files.append(self.json_reporter.generate_report(report_data, str(json_path)))
        
        if 'pdf' in formats and self.pdf_reporter:
            pdf_path = self.output_dir / f"sql_injection_report_{timestamp}.pdf"
            generated_files.append(self.pdf_reporter.generate_report(report_data, str(pdf_path)))
        elif 'pdf' in formats:
            self.logger.warning("PDF generation skipped - ReportLab not available")
        
        return generated_files
    
    def _create_default_summary(self, vulnerabilities: List[Vulnerability]) -> ScanSummary:
        """Create default scan summary"""
        high_risk = sum(1 for v in vulnerabilities if v.confidence >= 0.8)
        medium_risk = sum(1 for v in vulnerabilities if 0.5 <= v.confidence < 0.8)
        low_risk = sum(1 for v in vulnerabilities if v.confidence < 0.5)
        
        return ScanSummary(
            scan_date=datetime.datetime.now().isoformat(),
            target_url="Unknown",
            total_vectors_tested=0,
            vulnerabilities_found=len(vulnerabilities),
            high_risk_vulnerabilities=high_risk,
            medium_risk_vulnerabilities=medium_risk,
            low_risk_vulnerabilities=low_risk,
            scan_duration=0.0,
            databases_detected=list(set(v.database_type.value for v in vulnerabilities))
        )
