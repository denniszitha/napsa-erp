"""
Regulatory Reporting Automation Engine
Provides automated generation of regulatory reports for various compliance frameworks
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import json
import xml.etree.ElementTree as ET
from sqlalchemy.orm import Session
from sqlalchemy import text
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

logger = logging.getLogger(__name__)

class ReportType(Enum):
    """Types of regulatory reports"""
    SAR = "sar"  # Suspicious Activity Report
    CTR = "ctr"  # Currency Transaction Report
    FBAR = "fbar"  # Foreign Bank Account Report
    BSA = "bsa"  # Bank Secrecy Act Report
    CDD = "cdd"  # Customer Due Diligence Report
    EDD = "edd"  # Enhanced Due Diligence Report
    KYCRISK = "kyc_risk"  # KYC Risk Assessment Report
    SANCTIONS = "sanctions"  # Sanctions Screening Report
    PEP = "pep"  # Politically Exposed Persons Report
    WIRE_TRANSFER = "wire_transfer"  # Wire Transfer Report
    MONTHLY_COMPLIANCE = "monthly_compliance"
    QUARTERLY_COMPLIANCE = "quarterly_compliance"
    ANNUAL_COMPLIANCE = "annual_compliance"

class ReportFormat(Enum):
    """Report output formats"""
    PDF = "pdf"
    XML = "xml"
    CSV = "csv"
    JSON = "json"
    EXCEL = "xlsx"

class ReportStatus(Enum):
    """Report generation status"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    SUBMITTED = "submitted"

@dataclass
class ReportTemplate:
    """Report template configuration"""
    template_id: str
    name: str
    report_type: ReportType
    description: str
    fields: List[str]
    required_fields: List[str]
    format: ReportFormat
    frequency: str  # daily, weekly, monthly, quarterly, annually, on-demand
    regulatory_authority: str
    filing_deadline: Optional[str] = None
    template_version: str = "1.0"

@dataclass
class ReportInstance:
    """Generated report instance"""
    report_id: str
    template_id: str
    report_type: ReportType
    period_start: datetime
    period_end: datetime
    generated_at: datetime
    generated_by: str
    status: ReportStatus
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    record_count: int = 0
    metadata: Dict[str, Any] = None
    submission_deadline: Optional[datetime] = None
    submitted_at: Optional[datetime] = None

class RegulatorReportingEngine:
    """Main regulatory reporting engine"""
    
    def __init__(self):
        self.templates: Dict[str, ReportTemplate] = {}
        self.generated_reports: Dict[str, ReportInstance] = {}
        self._initialize_templates()
    
    def _initialize_templates(self):
        """Initialize predefined report templates"""
        
        # Suspicious Activity Report (SAR)
        sar_template = ReportTemplate(
            template_id="sar_standard",
            name="Suspicious Activity Report",
            report_type=ReportType.SAR,
            description="FinCEN SAR for suspicious activities",
            fields=[
                "filing_institution", "subject_information", "suspicious_activity",
                "transaction_details", "narrative", "filing_date", "contact_info"
            ],
            required_fields=[
                "filing_institution", "subject_information", "suspicious_activity",
                "transaction_details", "narrative"
            ],
            format=ReportFormat.XML,
            frequency="on-demand",
            regulatory_authority="FinCEN",
            filing_deadline="30 days from detection"
        )
        
        # Currency Transaction Report (CTR)
        ctr_template = ReportTemplate(
            template_id="ctr_standard",
            name="Currency Transaction Report",
            report_type=ReportType.CTR,
            description="FinCEN CTR for currency transactions over $10,000",
            fields=[
                "filing_institution", "transaction_date", "transaction_amount",
                "transaction_type", "customer_info", "account_info", "conductor_info"
            ],
            required_fields=[
                "filing_institution", "transaction_date", "transaction_amount",
                "customer_info"
            ],
            format=ReportFormat.XML,
            frequency="daily",
            regulatory_authority="FinCEN",
            filing_deadline="15 days after transaction"
        )
        
        # Monthly Compliance Report
        monthly_compliance = ReportTemplate(
            template_id="monthly_compliance",
            name="Monthly AML Compliance Report",
            report_type=ReportType.MONTHLY_COMPLIANCE,
            description="Monthly summary of AML compliance activities",
            fields=[
                "alert_statistics", "case_statistics", "training_completion",
                "system_performance", "regulatory_updates", "risk_assessment"
            ],
            required_fields=[
                "alert_statistics", "case_statistics", "system_performance"
            ],
            format=ReportFormat.PDF,
            frequency="monthly",
            regulatory_authority="Internal/Board",
            filing_deadline="5th of following month"
        )
        
        # KYC Risk Assessment Report
        kyc_risk_template = ReportTemplate(
            template_id="kyc_risk_assessment",
            name="KYC Risk Assessment Report",
            report_type=ReportType.KYCRISK,
            description="Customer risk assessment and profiling report",
            fields=[
                "customer_id", "risk_score", "risk_factors", "due_diligence_level",
                "review_date", "next_review_date", "documentation_status"
            ],
            required_fields=[
                "customer_id", "risk_score", "due_diligence_level"
            ],
            format=ReportFormat.EXCEL,
            frequency="quarterly",
            regulatory_authority="Internal/Auditors",
            filing_deadline="15 days after quarter end"
        )
        
        # Store templates
        for template in [sar_template, ctr_template, monthly_compliance, kyc_risk_template]:
            self.templates[template.template_id] = template
    
    def generate_report(self, template_id: str, period_start: datetime, 
                       period_end: datetime, generated_by: str, 
                       db: Session, parameters: Dict[str, Any] = None) -> str:
        """Generate a regulatory report"""
        try:
            if template_id not in self.templates:
                raise ValueError(f"Template {template_id} not found")
            
            template = self.templates[template_id]
            
            # Generate unique report ID
            report_id = f"{template_id}_{int(datetime.now().timestamp())}"
            
            # Create report instance
            report_instance = ReportInstance(
                report_id=report_id,
                template_id=template_id,
                report_type=template.report_type,
                period_start=period_start,
                period_end=period_end,
                generated_at=datetime.now(),
                generated_by=generated_by,
                status=ReportStatus.GENERATING,
                metadata=parameters or {}
            )
            
            self.generated_reports[report_id] = report_instance
            
            # Generate report based on type
            if template.report_type == ReportType.SAR:
                self._generate_sar_report(report_instance, db)
            elif template.report_type == ReportType.CTR:
                self._generate_ctr_report(report_instance, db)
            elif template.report_type == ReportType.MONTHLY_COMPLIANCE:
                self._generate_monthly_compliance_report(report_instance, db)
            elif template.report_type == ReportType.KYCRISK:
                self._generate_kyc_risk_report(report_instance, db)
            else:
                self._generate_generic_report(report_instance, db)
            
            report_instance.status = ReportStatus.COMPLETED
            logger.info(f"Report {report_id} generated successfully")
            
            return report_id
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            if report_id in self.generated_reports:
                self.generated_reports[report_id].status = ReportStatus.FAILED
            raise
    
    def _generate_sar_report(self, report_instance: ReportInstance, db: Session):
        """Generate Suspicious Activity Report"""
        try:
            template = self.templates[report_instance.template_id]
            
            # Query suspicious activities in the period
            query = """
            SELECT 
                a.id,
                a.title,
                a.description,
                a.severity,
                a.created_at,
                c.id as customer_id,
                c.first_name,
                c.last_name,
                c.date_of_birth,
                c.ssn,
                t.id as transaction_id,
                t.amount,
                t.transaction_date,
                t.country,
                t.description as transaction_desc
            FROM alerts a
            LEFT JOIN customers c ON a.customer_id = c.id
            LEFT JOIN transactions t ON a.transaction_id = t.id
            WHERE a.created_at BETWEEN :start_date AND :end_date
            AND a.severity IN ('HIGH', 'CRITICAL')
            ORDER BY a.created_at DESC
            """
            
            result = db.execute(text(query), {
                "start_date": report_instance.period_start,
                "end_date": report_instance.period_end
            })
            
            suspicious_activities = result.fetchall()
            report_instance.record_count = len(suspicious_activities)
            
            if template.format == ReportFormat.XML:
                content = self._create_sar_xml(suspicious_activities, report_instance)
                file_path = f"reports/sar_{report_instance.report_id}.xml"
            else:
                content = self._create_sar_pdf(suspicious_activities, report_instance)
                file_path = f"reports/sar_{report_instance.report_id}.pdf"
            
            # Save file (in production, save to file system or cloud storage)
            report_instance.file_path = file_path
            report_instance.file_size = len(content) if isinstance(content, (str, bytes)) else 0
            
            logger.info(f"SAR report generated with {report_instance.record_count} records")
            
        except Exception as e:
            logger.error(f"Error generating SAR report: {e}")
            raise
    
    def _generate_ctr_report(self, report_instance: ReportInstance, db: Session):
        """Generate Currency Transaction Report"""
        try:
            # Query currency transactions over $10,000 in the period
            query = """
            SELECT 
                t.id,
                t.amount,
                t.transaction_date,
                t.transaction_type,
                t.country,
                t.description,
                c.id as customer_id,
                c.first_name,
                c.last_name,
                c.date_of_birth,
                c.ssn,
                c.address,
                c.phone_number
            FROM transactions t
            JOIN customers c ON t.customer_id = c.id
            WHERE t.transaction_date BETWEEN :start_date AND :end_date
            AND t.amount >= 10000
            ORDER BY t.transaction_date DESC
            """
            
            result = db.execute(text(query), {
                "start_date": report_instance.period_start,
                "end_date": report_instance.period_end
            })
            
            ctr_transactions = result.fetchall()
            report_instance.record_count = len(ctr_transactions)
            
            template = self.templates[report_instance.template_id]
            
            if template.format == ReportFormat.XML:
                content = self._create_ctr_xml(ctr_transactions, report_instance)
                file_path = f"reports/ctr_{report_instance.report_id}.xml"
            else:
                content = self._create_ctr_csv(ctr_transactions, report_instance)
                file_path = f"reports/ctr_{report_instance.report_id}.csv"
            
            report_instance.file_path = file_path
            report_instance.file_size = len(content) if isinstance(content, (str, bytes)) else 0
            
            logger.info(f"CTR report generated with {report_instance.record_count} records")
            
        except Exception as e:
            logger.error(f"Error generating CTR report: {e}")
            raise
    
    def _generate_monthly_compliance_report(self, report_instance: ReportInstance, db: Session):
        """Generate monthly compliance report"""
        try:
            # Collect compliance statistics
            stats = self._collect_compliance_statistics(report_instance, db)
            
            # Generate PDF report
            content = self._create_compliance_pdf(stats, report_instance)
            file_path = f"reports/compliance_{report_instance.report_id}.pdf"
            
            report_instance.file_path = file_path
            report_instance.file_size = len(content) if isinstance(content, bytes) else 0
            report_instance.record_count = len(stats.get('alerts', []))
            
            logger.info(f"Monthly compliance report generated")
            
        except Exception as e:
            logger.error(f"Error generating monthly compliance report: {e}")
            raise
    
    def _generate_kyc_risk_report(self, report_instance: ReportInstance, db: Session):
        """Generate KYC risk assessment report"""
        try:
            # Query customer risk data
            query = """
            SELECT 
                c.id,
                c.first_name,
                c.last_name,
                c.risk_score,
                c.kyc_status,
                c.last_review_date,
                c.created_at,
                COUNT(t.id) as transaction_count,
                SUM(t.amount) as total_transaction_amount,
                MAX(t.transaction_date) as last_transaction_date
            FROM customers c
            LEFT JOIN transactions t ON c.id = t.customer_id
            WHERE c.created_at <= :end_date
            GROUP BY c.id, c.first_name, c.last_name, c.risk_score, c.kyc_status, c.last_review_date, c.created_at
            ORDER BY c.risk_score DESC
            """
            
            result = db.execute(text(query), {
                "end_date": report_instance.period_end
            })
            
            customer_data = result.fetchall()
            report_instance.record_count = len(customer_data)
            
            # Create Excel file
            content = self._create_kyc_excel(customer_data, report_instance)
            file_path = f"reports/kyc_risk_{report_instance.report_id}.xlsx"
            
            report_instance.file_path = file_path
            report_instance.file_size = len(content) if isinstance(content, bytes) else 0
            
            logger.info(f"KYC risk report generated with {report_instance.record_count} customers")
            
        except Exception as e:
            logger.error(f"Error generating KYC risk report: {e}")
            raise
    
    def _generate_generic_report(self, report_instance: ReportInstance, db: Session):
        """Generate generic report for unsupported types"""
        logger.warning(f"Generic report generated for unsupported type: {report_instance.report_type}")
        
        report_instance.record_count = 0
        report_instance.file_path = f"reports/generic_{report_instance.report_id}.txt"
        report_instance.file_size = 0
    
    def _create_sar_xml(self, activities: List, report_instance: ReportInstance) -> str:
        """Create SAR XML format"""
        root = ET.Element("SuspiciousActivityReport")
        root.set("xmlns", "http://www.fincen.gov/sar")
        
        # Header
        header = ET.SubElement(root, "Header")
        ET.SubElement(header, "ReportID").text = report_instance.report_id
        ET.SubElement(header, "GeneratedDate").text = report_instance.generated_at.isoformat()
        ET.SubElement(header, "PeriodStart").text = report_instance.period_start.isoformat()
        ET.SubElement(header, "PeriodEnd").text = report_instance.period_end.isoformat()
        
        # Filing institution
        institution = ET.SubElement(root, "FilingInstitution")
        ET.SubElement(institution, "Name").text = "NAPSA Financial Institution"
        ET.SubElement(institution, "Address").text = "123 Banking Street, Finance City"
        ET.SubElement(institution, "Phone").text = "(555) 123-4567"
        
        # Suspicious activities
        activities_elem = ET.SubElement(root, "SuspiciousActivities")
        
        for activity in activities:
            activity_elem = ET.SubElement(activities_elem, "SuspiciousActivity")
            ET.SubElement(activity_elem, "AlertID").text = str(activity[0])
            ET.SubElement(activity_elem, "Title").text = activity[1] or ""
            ET.SubElement(activity_elem, "Description").text = activity[2] or ""
            ET.SubElement(activity_elem, "Severity").text = activity[3] or ""
            ET.SubElement(activity_elem, "DetectedDate").text = activity[4].isoformat() if activity[4] else ""
            
            # Customer information
            if activity[5]:  # customer_id
                customer = ET.SubElement(activity_elem, "Customer")
                ET.SubElement(customer, "CustomerID").text = str(activity[5])
                ET.SubElement(customer, "FirstName").text = activity[6] or ""
                ET.SubElement(customer, "LastName").text = activity[7] or ""
                ET.SubElement(customer, "DateOfBirth").text = str(activity[8]) if activity[8] else ""
                ET.SubElement(customer, "SSN").text = activity[9] or ""
            
            # Transaction information
            if activity[10]:  # transaction_id
                transaction = ET.SubElement(activity_elem, "Transaction")
                ET.SubElement(transaction, "TransactionID").text = str(activity[10])
                ET.SubElement(transaction, "Amount").text = str(activity[11]) if activity[11] else ""
                ET.SubElement(transaction, "Date").text = activity[12].isoformat() if activity[12] else ""
                ET.SubElement(transaction, "Country").text = activity[13] or ""
                ET.SubElement(transaction, "Description").text = activity[14] or ""
        
        return ET.tostring(root, encoding='unicode')
    
    def _create_sar_pdf(self, activities: List, report_instance: ReportInstance) -> bytes:
        """Create SAR PDF format"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.darkblue
        )
        
        story = []
        
        # Title
        story.append(Paragraph("Suspicious Activity Report", title_style))
        story.append(Spacer(1, 12))
        
        # Report details
        story.append(Paragraph(f"Report ID: {report_instance.report_id}", styles['Normal']))
        story.append(Paragraph(f"Generated: {report_instance.generated_at.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Paragraph(f"Period: {report_instance.period_start.strftime('%Y-%m-%d')} to {report_instance.period_end.strftime('%Y-%m-%d')}", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Activities table
        if activities:
            data = [['Alert ID', 'Customer', 'Amount', 'Date', 'Severity']]
            
            for activity in activities[:50]:  # Limit for PDF
                customer_name = f"{activity[6] or ''} {activity[7] or ''}".strip()
                amount = f"${activity[11]:,.2f}" if activity[11] else "N/A"
                date = activity[12].strftime('%Y-%m-%d') if activity[12] else "N/A"
                
                data.append([
                    str(activity[0]),
                    customer_name[:20],
                    amount,
                    date,
                    activity[3] or ""
                ])
            
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
        
        doc.build(story)
        return buffer.getvalue()
    
    def _create_ctr_xml(self, transactions: List, report_instance: ReportInstance) -> str:
        """Create CTR XML format"""
        root = ET.Element("CurrencyTransactionReport")
        root.set("xmlns", "http://www.fincen.gov/ctr")
        
        # Header
        header = ET.SubElement(root, "Header")
        ET.SubElement(header, "ReportID").text = report_instance.report_id
        ET.SubElement(header, "GeneratedDate").text = report_instance.generated_at.isoformat()
        
        # Transactions
        transactions_elem = ET.SubElement(root, "Transactions")
        
        for txn in transactions:
            txn_elem = ET.SubElement(transactions_elem, "Transaction")
            ET.SubElement(txn_elem, "TransactionID").text = str(txn[0])
            ET.SubElement(txn_elem, "Amount").text = str(txn[1])
            ET.SubElement(txn_elem, "Date").text = txn[2].isoformat() if txn[2] else ""
            ET.SubElement(txn_elem, "Type").text = txn[3] or ""
            ET.SubElement(txn_elem, "Country").text = txn[4] or ""
            
            # Customer
            customer = ET.SubElement(txn_elem, "Customer")
            ET.SubElement(customer, "CustomerID").text = str(txn[6])
            ET.SubElement(customer, "FirstName").text = txn[7] or ""
            ET.SubElement(customer, "LastName").text = txn[8] or ""
            ET.SubElement(customer, "DateOfBirth").text = str(txn[9]) if txn[9] else ""
            ET.SubElement(customer, "SSN").text = txn[10] or ""
            ET.SubElement(customer, "Address").text = txn[11] or ""
            ET.SubElement(customer, "Phone").text = txn[12] or ""
        
        return ET.tostring(root, encoding='unicode')
    
    def _create_ctr_csv(self, transactions: List, report_instance: ReportInstance) -> str:
        """Create CTR CSV format"""
        df = pd.DataFrame(transactions, columns=[
            'transaction_id', 'amount', 'transaction_date', 'transaction_type',
            'country', 'description', 'customer_id', 'first_name', 'last_name',
            'date_of_birth', 'ssn', 'address', 'phone_number'
        ])
        
        return df.to_csv(index=False)
    
    def _collect_compliance_statistics(self, report_instance: ReportInstance, db: Session) -> Dict[str, Any]:
        """Collect compliance statistics for monthly report"""
        try:
            stats = {}
            
            # Alert statistics
            alert_query = """
            SELECT 
                severity,
                COUNT(*) as count,
                AVG(EXTRACT(EPOCH FROM (resolved_at - created_at))/3600) as avg_resolution_hours
            FROM alerts 
            WHERE created_at BETWEEN :start_date AND :end_date
            GROUP BY severity
            """
            
            result = db.execute(text(alert_query), {
                "start_date": report_instance.period_start,
                "end_date": report_instance.period_end
            })
            
            stats['alerts'] = [dict(row._mapping) for row in result]
            
            # Transaction statistics
            txn_query = """
            SELECT 
                COUNT(*) as total_transactions,
                SUM(amount) as total_amount,
                AVG(amount) as avg_amount,
                COUNT(DISTINCT customer_id) as unique_customers
            FROM transactions 
            WHERE transaction_date BETWEEN :start_date AND :end_date
            """
            
            result = db.execute(text(txn_query), {
                "start_date": report_instance.period_start,
                "end_date": report_instance.period_end
            })
            
            stats['transactions'] = dict(result.fetchone()._mapping)
            
            # Customer risk distribution
            risk_query = """
            SELECT 
                CASE 
                    WHEN risk_score >= 80 THEN 'High'
                    WHEN risk_score >= 50 THEN 'Medium' 
                    ELSE 'Low'
                END as risk_category,
                COUNT(*) as count
            FROM customers 
            GROUP BY risk_category
            """
            
            result = db.execute(text(risk_query))
            stats['risk_distribution'] = [dict(row._mapping) for row in result]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error collecting compliance statistics: {e}")
            return {}
    
    def _create_compliance_pdf(self, stats: Dict[str, Any], report_instance: ReportInstance) -> bytes:
        """Create compliance PDF report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.darkblue,
            alignment=1  # Center alignment
        )
        
        story = []
        
        # Title
        story.append(Paragraph("Monthly AML Compliance Report", title_style))
        story.append(Spacer(1, 20))
        
        # Report metadata
        story.append(Paragraph(f"Report Period: {report_instance.period_start.strftime('%B %Y')}", styles['Heading2']))
        story.append(Paragraph(f"Generated: {report_instance.generated_at.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Alert statistics
        if stats.get('alerts'):
            story.append(Paragraph("Alert Statistics", styles['Heading2']))
            
            alert_data = [['Severity', 'Count', 'Avg Resolution (hours)']]
            for alert in stats['alerts']:
                alert_data.append([
                    alert['severity'],
                    str(alert['count']),
                    f"{alert['avg_resolution_hours']:.1f}" if alert['avg_resolution_hours'] else "N/A"
                ])
            
            alert_table = Table(alert_data)
            alert_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(alert_table)
            story.append(Spacer(1, 12))
        
        # Transaction statistics
        if stats.get('transactions'):
            story.append(Paragraph("Transaction Statistics", styles['Heading2']))
            
            txn_stats = stats['transactions']
            story.append(Paragraph(f"Total Transactions: {txn_stats.get('total_transactions', 0):,}", styles['Normal']))
            story.append(Paragraph(f"Total Amount: ${txn_stats.get('total_amount', 0):,.2f}", styles['Normal']))
            story.append(Paragraph(f"Average Amount: ${txn_stats.get('avg_amount', 0):,.2f}", styles['Normal']))
            story.append(Paragraph(f"Unique Customers: {txn_stats.get('unique_customers', 0):,}", styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Risk distribution
        if stats.get('risk_distribution'):
            story.append(Paragraph("Customer Risk Distribution", styles['Heading2']))
            
            risk_data = [['Risk Category', 'Count']]
            for risk in stats['risk_distribution']:
                risk_data.append([risk['risk_category'], str(risk['count'])])
            
            risk_table = Table(risk_data)
            risk_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(risk_table)
        
        doc.build(story)
        return buffer.getvalue()
    
    def _create_kyc_excel(self, customer_data: List, report_instance: ReportInstance) -> bytes:
        """Create KYC Excel report"""
        df = pd.DataFrame(customer_data, columns=[
            'customer_id', 'first_name', 'last_name', 'risk_score', 'kyc_status',
            'last_review_date', 'created_at', 'transaction_count', 
            'total_transaction_amount', 'last_transaction_date'
        ])
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='KYC Risk Assessment', index=False)
        
        return buffer.getvalue()
    
    def get_report_status(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get report generation status"""
        if report_id not in self.generated_reports:
            return None
        
        report = self.generated_reports[report_id]
        template = self.templates.get(report.template_id)
        
        return {
            "report_id": report.report_id,
            "template_id": report.template_id,
            "template_name": template.name if template else "Unknown",
            "report_type": report.report_type.value,
            "status": report.status.value,
            "period_start": report.period_start.isoformat(),
            "period_end": report.period_end.isoformat(),
            "generated_at": report.generated_at.isoformat(),
            "generated_by": report.generated_by,
            "record_count": report.record_count,
            "file_path": report.file_path,
            "file_size": report.file_size,
            "submission_deadline": report.submission_deadline.isoformat() if report.submission_deadline else None,
            "submitted_at": report.submitted_at.isoformat() if report.submitted_at else None,
            "metadata": report.metadata
        }
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get available report templates"""
        templates = []
        for template_id, template in self.templates.items():
            templates.append({
                "template_id": template_id,
                "name": template.name,
                "report_type": template.report_type.value,
                "description": template.description,
                "format": template.format.value,
                "frequency": template.frequency,
                "regulatory_authority": template.regulatory_authority,
                "filing_deadline": template.filing_deadline,
                "required_fields": template.required_fields
            })
        
        return templates
    
    def get_reports_by_period(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get reports generated in a specific period"""
        reports = []
        for report_id, report in self.generated_reports.items():
            if start_date <= report.generated_at <= end_date:
                report_info = self.get_report_status(report_id)
                if report_info:
                    reports.append(report_info)
        
        return sorted(reports, key=lambda x: x['generated_at'], reverse=True)
    
    def get_compliance_calendar(self, year: int, month: int = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get compliance reporting calendar"""
        calendar_items = []
        
        # Add template-based deadlines
        for template in self.templates.values():
            if template.filing_deadline and template.frequency != "on-demand":
                calendar_items.append({
                    "template_id": template.template_id,
                    "name": template.name,
                    "type": template.report_type.value,
                    "frequency": template.frequency,
                    "deadline": template.filing_deadline,
                    "authority": template.regulatory_authority
                })
        
        # Group by frequency for the calendar
        return {
            "year": year,
            "month": month,
            "items": calendar_items
        }

# Global reporting engine instance
reporting_engine = None

def get_reporting_engine() -> RegulatorReportingEngine:
    """Get the global regulatory reporting engine instance"""
    global reporting_engine
    if reporting_engine is None:
        reporting_engine = RegulatorReportingEngine()
    return reporting_engine