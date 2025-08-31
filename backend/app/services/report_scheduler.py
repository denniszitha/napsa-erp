"""
Automated Report Scheduling Service for NAPSA ERM
Provides scheduled report generation and distribution capabilities
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
import json
from pathlib import Path
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from app.core.database import get_db
from app.services.advanced_reports import advanced_report_service
from app.services.reports import report_service
from app.models.user import User

logger = logging.getLogger(__name__)

class ReportFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"

class ReportType(str, Enum):
    EXECUTIVE_DASHBOARD = "executive_dashboard"
    RISK_REGISTER = "risk_register"
    KRI_REPORT = "kri_report"
    COMPLIANCE_REPORT = "compliance_report"
    INCIDENT_SUMMARY = "incident_summary"
    ASSESSMENT_REPORT = "assessment_report"

class ReportFormat(str, Enum):
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"

class ScheduledReport:
    def __init__(self, report_config: Dict[str, Any]):
        self.id = report_config.get('id')
        self.name = report_config.get('name')
        self.description = report_config.get('description')
        self.report_type = ReportType(report_config.get('report_type'))
        self.frequency = ReportFrequency(report_config.get('frequency'))
        self.format = ReportFormat(report_config.get('format', 'pdf'))
        self.recipients = report_config.get('recipients', [])
        self.parameters = report_config.get('parameters', {})
        self.enabled = report_config.get('enabled', True)
        self.last_run = report_config.get('last_run')
        self.next_run = report_config.get('next_run')
        self.created_by = report_config.get('created_by')
        self.created_at = report_config.get('created_at')

class ReportSchedulerService:
    def __init__(self):
        self.scheduled_reports: Dict[str, ScheduledReport] = {}
        self.config_file = Path('/app/config/scheduled_reports.json')
        self.running = False
        self._load_scheduled_reports()

    def _load_scheduled_reports(self):
        """Load scheduled reports from configuration file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    reports_config = json.load(f)
                    
                for report_id, config in reports_config.items():
                    self.scheduled_reports[report_id] = ScheduledReport(config)
                    
            else:
                # Create default scheduled reports
                self._create_default_reports()
                
        except Exception as e:
            logger.error(f"Error loading scheduled reports: {e}")
            self._create_default_reports()

    def _create_default_reports(self):
        """Create default scheduled reports for NAPSA"""
        default_reports = {
            "executive_monthly": {
                "id": "executive_monthly",
                "name": "Executive Monthly Dashboard",
                "description": "Monthly executive summary report for senior management",
                "report_type": ReportType.EXECUTIVE_DASHBOARD.value,
                "frequency": ReportFrequency.MONTHLY.value,
                "format": ReportFormat.PDF.value,
                "recipients": ["ceo@napsa.co.zm", "riskmanager@napsa.co.zm"],
                "parameters": {"date_range": 30},
                "enabled": True,
                "next_run": self._calculate_next_run(ReportFrequency.MONTHLY),
                "created_by": "system",
                "created_at": datetime.now().isoformat()
            },
            "risk_register_weekly": {
                "id": "risk_register_weekly",
                "name": "Weekly Risk Register Update",
                "description": "Weekly risk register report for risk committee",
                "report_type": ReportType.RISK_REGISTER.value,
                "frequency": ReportFrequency.WEEKLY.value,
                "format": ReportFormat.EXCEL.value,
                "recipients": ["riskcommittee@napsa.co.zm"],
                "parameters": {},
                "enabled": True,
                "next_run": self._calculate_next_run(ReportFrequency.WEEKLY),
                "created_by": "system",
                "created_at": datetime.now().isoformat()
            },
            "kri_daily": {
                "id": "kri_daily",
                "name": "Daily KRI Monitoring",
                "description": "Daily KRI status report for risk officers",
                "report_type": ReportType.KRI_REPORT.value,
                "frequency": ReportFrequency.DAILY.value,
                "format": ReportFormat.PDF.value,
                "recipients": ["riskofficers@napsa.co.zm"],
                "parameters": {},
                "enabled": True,
                "next_run": self._calculate_next_run(ReportFrequency.DAILY),
                "created_by": "system",
                "created_at": datetime.now().isoformat()
            },
            "compliance_quarterly": {
                "id": "compliance_quarterly",
                "name": "Quarterly Compliance Report",
                "description": "Quarterly compliance status report for board",
                "report_type": ReportType.COMPLIANCE_REPORT.value,
                "frequency": ReportFrequency.QUARTERLY.value,
                "format": ReportFormat.PDF.value,
                "recipients": ["board@napsa.co.zm", "compliance@napsa.co.zm"],
                "parameters": {},
                "enabled": True,
                "next_run": self._calculate_next_run(ReportFrequency.QUARTERLY),
                "created_by": "system",
                "created_at": datetime.now().isoformat()
            }
        }
        
        for report_id, config in default_reports.items():
            self.scheduled_reports[report_id] = ScheduledReport(config)
        
        self._save_scheduled_reports()

    def _save_scheduled_reports(self):
        """Save scheduled reports to configuration file"""
        try:
            # Ensure config directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            reports_config = {}
            for report_id, report in self.scheduled_reports.items():
                reports_config[report_id] = {
                    "id": report.id,
                    "name": report.name,
                    "description": report.description,
                    "report_type": report.report_type.value,
                    "frequency": report.frequency.value,
                    "format": report.format.value,
                    "recipients": report.recipients,
                    "parameters": report.parameters,
                    "enabled": report.enabled,
                    "last_run": report.last_run,
                    "next_run": report.next_run,
                    "created_by": report.created_by,
                    "created_at": report.created_at
                }
            
            with open(self.config_file, 'w') as f:
                json.dump(reports_config, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving scheduled reports: {e}")

    def _calculate_next_run(self, frequency: ReportFrequency) -> str:
        """Calculate next run time based on frequency"""
        now = datetime.now()
        
        if frequency == ReportFrequency.DAILY:
            next_run = now.replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=1)
        elif frequency == ReportFrequency.WEEKLY:
            # Every Monday at 8 AM
            days_ahead = 0 - now.weekday()  # Monday is 0
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            next_run = now.replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=days_ahead)
        elif frequency == ReportFrequency.MONTHLY:
            # First day of next month at 8 AM
            if now.month == 12:
                next_run = now.replace(year=now.year+1, month=1, day=1, hour=8, minute=0, second=0, microsecond=0)
            else:
                next_run = now.replace(month=now.month+1, day=1, hour=8, minute=0, second=0, microsecond=0)
        elif frequency == ReportFrequency.QUARTERLY:
            # First day of next quarter at 8 AM
            quarter_start_months = [1, 4, 7, 10]
            current_quarter = (now.month - 1) // 3
            next_quarter_month = quarter_start_months[(current_quarter + 1) % 4]
            
            if next_quarter_month == 1:  # Next year
                next_run = now.replace(year=now.year+1, month=1, day=1, hour=8, minute=0, second=0, microsecond=0)
            else:
                next_run = now.replace(month=next_quarter_month, day=1, hour=8, minute=0, second=0, microsecond=0)
        else:  # ANNUALLY
            next_run = now.replace(year=now.year+1, month=1, day=1, hour=8, minute=0, second=0, microsecond=0)
        
        return next_run.isoformat()

    async def start_scheduler(self):
        """Start the report scheduler"""
        if self.running:
            return
            
        self.running = True
        logger.info("Starting report scheduler...")
        
        while self.running:
            try:
                await self._check_and_run_reports()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(300)

    def stop_scheduler(self):
        """Stop the report scheduler"""
        self.running = False
        logger.info("Report scheduler stopped")

    async def _check_and_run_reports(self):
        """Check for due reports and execute them"""
        now = datetime.now()
        
        for report in self.scheduled_reports.values():
            if not report.enabled:
                continue
                
            if report.next_run and datetime.fromisoformat(report.next_run) <= now:
                try:
                    await self._execute_report(report)
                    report.last_run = now.isoformat()
                    report.next_run = self._calculate_next_run(report.frequency)
                    self._save_scheduled_reports()
                    
                except Exception as e:
                    logger.error(f"Error executing scheduled report {report.id}: {e}")

    async def _execute_report(self, report: ScheduledReport):
        """Execute a scheduled report"""
        logger.info(f"Executing scheduled report: {report.name}")
        
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Generate report based on type
            if report.report_type == ReportType.EXECUTIVE_DASHBOARD:
                report_data = await self._generate_executive_dashboard(db, report)
            elif report.report_type == ReportType.RISK_REGISTER:
                report_data = await self._generate_risk_register(db, report)
            elif report.report_type == ReportType.KRI_REPORT:
                report_data = await self._generate_kri_report(db, report)
            elif report.report_type == ReportType.COMPLIANCE_REPORT:
                report_data = await self._generate_compliance_report(db, report)
            else:
                logger.warning(f"Unknown report type: {report.report_type}")
                return
            
            # Send report to recipients
            await self._send_report(report, report_data)
            
        finally:
            db.close()

    async def _generate_executive_dashboard(self, db: Session, report: ScheduledReport) -> bytes:
        """Generate executive dashboard report"""
        date_range = report.parameters.get('date_range', 30)
        return advanced_report_service.generate_executive_dashboard(db, "System", date_range)

    async def _generate_risk_register(self, db: Session, report: ScheduledReport) -> bytes:
        """Generate risk register report"""
        return report_service.generate_risk_report(db, "System")

    async def _generate_kri_report(self, db: Session, report: ScheduledReport) -> bytes:
        """Generate KRI report"""
        return report_service.generate_kri_report(db)

    async def _generate_compliance_report(self, db: Session, report: ScheduledReport) -> bytes:
        """Generate compliance report"""
        # Placeholder - would implement actual compliance report generation
        return b"Compliance report placeholder"

    async def _send_report(self, report: ScheduledReport, report_data: bytes):
        """Send report to recipients via email"""
        try:
            # Email configuration (should be in environment variables)
            smtp_server = "smtp.gmail.com"  # Configure as needed
            smtp_port = 587
            smtp_username = "reports@napsa.co.zm"  # Configure as needed
            smtp_password = "password"  # Configure as needed - use env variable
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['Subject'] = f"NAPSA ERM Automated Report: {report.name}"
            
            # Email body
            body = f"""
Dear Team,

Please find attached the automated report: {report.name}

Report Description: {report.description}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Frequency: {report.frequency.value.title()}

This is an automated message from the NAPSA Enterprise Risk Management System.

Best regards,
NAPSA ERM System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach report
            filename = f"{report.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.{report.format.value}"
            attachment = MIMEApplication(report_data, _subtype=report.format.value)
            attachment.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(attachment)
            
            # Send to each recipient
            for recipient in report.recipients:
                msg['To'] = recipient
                
                # Connect and send (in production, use proper email service)
                # For now, just log the action
                logger.info(f"Would send report {report.name} to {recipient}")
                # 
                # with smtplib.SMTP(smtp_server, smtp_port) as server:
                #     server.starttls()
                #     server.login(smtp_username, smtp_password)
                #     server.send_message(msg)
                
                del msg['To']
                
        except Exception as e:
            logger.error(f"Error sending report {report.name}: {e}")

    def add_scheduled_report(self, report_config: Dict[str, Any]) -> str:
        """Add a new scheduled report"""
        report_id = report_config.get('id', f"report_{len(self.scheduled_reports) + 1}")
        report_config['id'] = report_id
        report_config['created_at'] = datetime.now().isoformat()
        report_config['next_run'] = self._calculate_next_run(ReportFrequency(report_config['frequency']))
        
        self.scheduled_reports[report_id] = ScheduledReport(report_config)
        self._save_scheduled_reports()
        
        logger.info(f"Added scheduled report: {report_config['name']}")
        return report_id

    def update_scheduled_report(self, report_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing scheduled report"""
        if report_id not in self.scheduled_reports:
            return False
        
        report = self.scheduled_reports[report_id]
        
        # Update fields
        if 'name' in updates:
            report.name = updates['name']
        if 'description' in updates:
            report.description = updates['description']
        if 'enabled' in updates:
            report.enabled = updates['enabled']
        if 'recipients' in updates:
            report.recipients = updates['recipients']
        if 'parameters' in updates:
            report.parameters = updates['parameters']
        if 'frequency' in updates:
            report.frequency = ReportFrequency(updates['frequency'])
            report.next_run = self._calculate_next_run(report.frequency)
        
        self._save_scheduled_reports()
        logger.info(f"Updated scheduled report: {report_id}")
        return True

    def delete_scheduled_report(self, report_id: str) -> bool:
        """Delete a scheduled report"""
        if report_id in self.scheduled_reports:
            del self.scheduled_reports[report_id]
            self._save_scheduled_reports()
            logger.info(f"Deleted scheduled report: {report_id}")
            return True
        return False

    def get_scheduled_reports(self) -> List[Dict[str, Any]]:
        """Get all scheduled reports"""
        reports = []
        for report in self.scheduled_reports.values():
            reports.append({
                "id": report.id,
                "name": report.name,
                "description": report.description,
                "report_type": report.report_type.value,
                "frequency": report.frequency.value,
                "format": report.format.value,
                "recipients": report.recipients,
                "enabled": report.enabled,
                "last_run": report.last_run,
                "next_run": report.next_run,
                "created_by": report.created_by,
                "created_at": report.created_at
            })
        return reports

    def run_report_now(self, report_id: str) -> bool:
        """Manually trigger a report to run immediately"""
        if report_id not in self.scheduled_reports:
            return False
        
        report = self.scheduled_reports[report_id]
        
        # Run the report in background
        asyncio.create_task(self._execute_report(report))
        logger.info(f"Manual execution triggered for report: {report.name}")
        return True

# Global instance
report_scheduler_service = ReportSchedulerService()