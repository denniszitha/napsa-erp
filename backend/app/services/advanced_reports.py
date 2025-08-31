"""
Advanced Reporting Service for NAPSA ERM
Provides comprehensive reporting capabilities including executive dashboards,
automated scheduling, and advanced analytics
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, 
    Image, KeepTogether, NextPageTemplate, PageTemplate, Frame
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics import renderPDF

import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import json
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_

# Import all models
from app.models.risk import Risk, RiskStatus, RiskCategoryEnum
from app.models.control import Control, ControlStatus, ControlType
from app.models.kri import KeyRiskIndicator, KRIStatus, KRIFrequency
from app.models.incident import Incident, IncidentStatus, IncidentSeverity
from app.models.assessment import RiskAssessment
from app.models.user import User, UserRole
from app.models.workflow import RiskTreatment, TreatmentStatus, TreatmentStrategy

logger = logging.getLogger(__name__)

class AdvancedReportService:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Setup custom report styles"""
        # NAPSA Brand colors
        self.primary_color = colors.HexColor('#1e3a8a')  # NAPSA Blue
        self.secondary_color = colors.HexColor('#f59e0b')  # NAPSA Gold
        self.accent_color = colors.HexColor('#10b981')   # Success Green
        self.warning_color = colors.HexColor('#f59e0b')  # Warning Orange
        self.danger_color = colors.HexColor('#ef4444')   # Danger Red
        
        # Custom styles
        self.title_style = ParagraphStyle(
            'NAPSATitle',
            parent=self.styles['Heading1'],
            fontSize=26,
            textColor=self.primary_color,
            alignment=TA_CENTER,
            spaceAfter=30,
            fontName='Helvetica-Bold'
        )
        
        self.subtitle_style = ParagraphStyle(
            'NAPSASubtitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=self.primary_color,
            alignment=TA_LEFT,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        )
        
        self.executive_summary_style = ParagraphStyle(
            'ExecutiveSummary',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.black,
            alignment=TA_JUSTIFY,
            spaceAfter=15,
            leftIndent=20,
            rightIndent=20
        )
        
        self.highlight_style = ParagraphStyle(
            'Highlight',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=self.primary_color,
            alignment=TA_CENTER,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )

    def generate_executive_dashboard(self, db: Session, user_name: str, date_range: int = 30) -> bytes:
        """Generate comprehensive executive dashboard report"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        
        # Header with NAPSA branding
        story.append(self._create_header("NAPSA ERM Executive Dashboard", user_name))
        story.append(Spacer(1, 0.3*inch))
        
        # Executive Summary Section
        story.append(Paragraph("Executive Summary", self.subtitle_style))
        executive_summary = self._generate_executive_summary(db, date_range)
        story.append(Paragraph(executive_summary, self.executive_summary_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Key Metrics Dashboard
        story.append(self._create_key_metrics_section(db))
        story.append(PageBreak())
        
        # Risk Heat Map
        story.append(Paragraph("Risk Portfolio Analysis", self.subtitle_style))
        story.append(self._create_risk_heatmap_table(db))
        story.append(Spacer(1, 0.3*inch))
        
        # Top Risk Issues
        story.append(self._create_top_risks_section(db))
        story.append(PageBreak())
        
        # KRI Dashboard
        story.append(Paragraph("Key Risk Indicators Status", self.subtitle_style))
        story.append(self._create_kri_dashboard(db))
        story.append(PageBreak())
        
        # Incident Summary
        story.append(Paragraph("Incident Management Summary", self.subtitle_style))
        story.append(self._create_incident_summary(db, date_range))
        story.append(PageBreak())
        
        # Compliance Overview
        story.append(Paragraph("Compliance Status Overview", self.subtitle_style))
        story.append(self._create_compliance_overview(db))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.read()

    def _create_header(self, title: str, user_name: str) -> Table:
        """Create professional report header"""
        header_data = [
            [Paragraph(title, self.title_style), ''],
            [f"Generated: {datetime.now().strftime('%d %B %Y at %H:%M')}", f"Prepared by: {user_name}"],
            ['National Pension Scheme Authority', 'Enterprise Risk Management System']
        ]
        
        header_table = Table(header_data, colWidths=[4*inch, 3*inch])
        header_table.setStyle(TableStyle([
            ('SPAN', (0, 0), (1, 0)),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('FONTSIZE', (0, 1), (1, 2), 9),
            ('TEXTCOLOR', (0, 1), (1, 2), colors.grey),
            ('BOTTOMPADDING', (0, 0), (1, 0), 20),
            ('BOTTOMPADDING', (0, 1), (1, 2), 5),
        ]))
        
        return header_table

    def _generate_executive_summary(self, db: Session, date_range: int) -> str:
        """Generate executive summary text"""
        # Get key statistics
        total_risks = db.query(Risk).count()
        high_risks = db.query(Risk).filter(Risk.inherent_risk_score >= 15).count()
        active_incidents = db.query(Incident).filter(
            Incident.status == IncidentStatus.open,
            Incident.created_at >= datetime.now() - timedelta(days=date_range)
        ).count()
        
        overdue_treatments = db.query(RiskTreatment).filter(
            RiskTreatment.target_date < datetime.now(),
            RiskTreatment.status != TreatmentStatus.completed
        ).count()
        
        summary = f"""
        During the {date_range}-day period ending {datetime.now().strftime('%B %d, %Y')}, 
        NAPSA's Enterprise Risk Management system tracked {total_risks} identified risks across all business units. 
        Of these, {high_risks} risks are classified as high priority requiring executive attention.
        
        The organization has {active_incidents} active incidents under management, demonstrating our proactive 
        approach to risk monitoring and response. However, {overdue_treatments} risk treatment activities 
        are currently overdue and require immediate management attention to ensure continued risk mitigation effectiveness.
        
        This report provides a comprehensive overview of the current risk landscape, key performance indicators, 
        and recommended actions to maintain NAPSA's risk profile within acceptable tolerances.
        """
        
        return summary.strip()

    def _create_key_metrics_section(self, db: Session) -> KeepTogether:
        """Create key metrics summary table"""
        # Calculate metrics
        total_risks = db.query(Risk).count()
        active_risks = db.query(Risk).filter(Risk.status == RiskStatus.active).count()
        high_risks = db.query(Risk).filter(Risk.inherent_risk_score >= 15).count()
        critical_risks = db.query(Risk).filter(Risk.inherent_risk_score >= 20).count()
        
        total_controls = db.query(Control).count()
        effective_controls = db.query(Control).filter(Control.status == ControlStatus.effective).count()
        
        total_kris = db.query(KeyRiskIndicator).count()
        breached_kris = db.query(KeyRiskIndicator).filter(KRIStatus.critical).count()
        
        open_incidents = db.query(Incident).filter(Incident.status == IncidentStatus.open).count()
        
        # Create metrics table
        metrics_data = [
            ['Risk Management Metrics', 'Current Status', 'Risk Level'],
            ['Total Identified Risks', str(total_risks), self._get_risk_level_indicator(total_risks, 50, 100)],
            ['Active Risks', str(active_risks), self._get_risk_level_indicator(active_risks, 30, 60)],
            ['High Priority Risks', str(high_risks), self._get_risk_level_indicator(high_risks, 5, 15)],
            ['Critical Risks', str(critical_risks), self._get_risk_level_indicator(critical_risks, 1, 5)],
            ['', '', ''],
            ['Control Effectiveness', '', ''],
            ['Total Controls', str(total_controls), 'INFO'],
            ['Effective Controls', str(effective_controls), 'INFO'],
            ['Control Effectiveness Rate', f"{(effective_controls/total_controls*100):.1f}%" if total_controls > 0 else "N/A", 
             self._get_percentage_indicator(effective_controls/total_controls*100 if total_controls > 0 else 0)],
            ['', '', ''],
            ['Monitoring & Incidents', '', ''],
            ['Key Risk Indicators', str(total_kris), 'INFO'],
            ['KRIs in Breach', str(breached_kris), self._get_risk_level_indicator(breached_kris, 1, 3)],
            ['Open Incidents', str(open_incidents), self._get_risk_level_indicator(open_incidents, 2, 5)]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[3*inch, 1.5*inch, 1.2*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            # Style for section headers
            ('BACKGROUND', (0, 6), (-1, 6), colors.lightgrey),
            ('BACKGROUND', (0, 11), (-1, 11), colors.lightgrey),
            ('FONTNAME', (0, 6), (0, 6), 'Helvetica-Bold'),
            ('FONTNAME', (0, 11), (0, 11), 'Helvetica-Bold'),
            # Empty rows
            ('GRID', (0, 5), (-1, 5), 0, colors.white),
            ('GRID', (0, 10), (-1, 10), 0, colors.white),
        ]))
        
        return KeepTogether([
            Paragraph("Key Performance Metrics", self.subtitle_style),
            metrics_table,
            Spacer(1, 0.3*inch)
        ])

    def _get_risk_level_indicator(self, value: int, medium_threshold: int, high_threshold: int) -> str:
        """Get risk level indicator text"""
        if value >= high_threshold:
            return "HIGH"
        elif value >= medium_threshold:
            return "MEDIUM"
        else:
            return "LOW"
            
    def _get_percentage_indicator(self, percentage: float) -> str:
        """Get percentage-based indicator"""
        if percentage >= 80:
            return "EXCELLENT"
        elif percentage >= 60:
            return "GOOD"
        elif percentage >= 40:
            return "FAIR"
        else:
            return "POOR"

    def _create_risk_heatmap_table(self, db: Session) -> Table:
        """Create risk heatmap visualization as table"""
        # Get active risks
        risks = db.query(Risk).filter(Risk.status == RiskStatus.active).all()
        
        # Create 5x5 heatmap matrix
        heatmap = {}
        for i in range(1, 6):
            for j in range(1, 6):
                heatmap[(i, j)] = []
        
        # Populate heatmap
        for risk in risks:
            if risk.likelihood and risk.impact:
                key = (risk.likelihood, risk.impact)
                if key in heatmap:
                    heatmap[key].append(risk.title[:30] + '...' if len(risk.title) > 30 else risk.title)
        
        # Create table data
        heatmap_data = [['Impact →\nLikelihood ↓', 'Very Low (1)', 'Low (2)', 'Medium (3)', 'High (4)', 'Very High (5)']]
        
        for likelihood in range(5, 0, -1):  # From 5 to 1
            row = [f'{self._get_likelihood_label(likelihood)} ({likelihood})']
            for impact in range(1, 6):  # From 1 to 5
                risk_count = len(heatmap.get((likelihood, impact), []))
                cell_text = str(risk_count) if risk_count > 0 else '-'
                row.append(cell_text)
            heatmap_data.append(row)
        
        heatmap_table = Table(heatmap_data, colWidths=[1.2*inch] + [1*inch]*5)
        
        # Style the heatmap with colors based on risk level
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('BACKGROUND', (0, 0), (0, -1), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]
        
        # Add color coding for risk levels
        for likelihood in range(1, 6):
            for impact in range(1, 6):
                row_idx = 6 - likelihood  # Convert to table row index
                col_idx = impact
                score = likelihood * impact
                
                if score >= 20:
                    bg_color = colors.red
                elif score >= 15:
                    bg_color = colors.orange
                elif score >= 10:
                    bg_color = colors.yellow
                elif score >= 5:
                    bg_color = colors.lightgreen
                else:
                    bg_color = colors.lightgrey
                    
                table_style.append(('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), bg_color))
        
        heatmap_table.setStyle(TableStyle(table_style))
        return heatmap_table

    def _get_likelihood_label(self, likelihood: int) -> str:
        """Get likelihood label"""
        labels = {1: 'Very Low', 2: 'Low', 3: 'Medium', 4: 'High', 5: 'Very High'}
        return labels.get(likelihood, 'Unknown')

    def _create_top_risks_section(self, db: Session) -> KeepTogether:
        """Create top risks section"""
        # Get top 10 highest scoring active risks
        top_risks = db.query(Risk).filter(
            Risk.status == RiskStatus.active
        ).order_by(desc(Risk.inherent_risk_score)).limit(10).all()
        
        risk_data = [['Rank', 'Risk Title', 'Category', 'Score', 'Owner', 'Status']]
        
        for idx, risk in enumerate(top_risks, 1):
            owner_name = risk.owner.full_name if risk.owner else 'Unassigned'
            risk_data.append([
                str(idx),
                risk.title[:40] + '...' if len(risk.title) > 40 else risk.title,
                risk.category.value if risk.category else 'N/A',
                str(risk.inherent_risk_score),
                owner_name[:20] + '...' if len(owner_name) > 20 else owner_name,
                risk.status.value
            ])
        
        risk_table = Table(risk_data, colWidths=[0.5*inch, 2.8*inch, 1*inch, 0.6*inch, 1.5*inch, 0.8*inch])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ]))
        
        return KeepTogether([
            Paragraph("Top 10 Highest Priority Risks", self.subtitle_style),
            risk_table,
            Spacer(1, 0.2*inch)
        ])

    def _create_kri_dashboard(self, db: Session) -> Table:
        """Create KRI dashboard table"""
        kris = db.query(KeyRiskIndicator).all()
        
        kri_data = [['KRI Name', 'Current Value', 'Target', 'Threshold', 'Status', 'Trend', 'Last Updated']]
        
        for kri in kris:
            status_display = kri.status.value.upper() if kri.status else 'UNKNOWN'
            trend_display = kri.trend or 'STABLE'
            last_updated = kri.updated_at.strftime('%Y-%m-%d') if kri.updated_at else 'N/A'
            
            kri_data.append([
                kri.name[:25] + '...' if len(kri.name) > 25 else kri.name,
                f"{kri.current_value:.1f}" if kri.current_value else "N/A",
                f"{kri.target_value:.1f}" if kri.target_value else "N/A",
                f"{kri.threshold_value:.1f}" if kri.threshold_value else "N/A",
                status_display,
                trend_display.upper(),
                last_updated
            ])
        
        kri_table = Table(kri_data, colWidths=[1.8*inch, 0.8*inch, 0.7*inch, 0.7*inch, 0.8*inch, 0.7*inch, 0.8*inch])
        kri_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ]))
        
        return kri_table

    def _create_incident_summary(self, db: Session, date_range: int) -> Table:
        """Create incident summary table"""
        cutoff_date = datetime.now() - timedelta(days=date_range)
        recent_incidents = db.query(Incident).filter(
            Incident.created_at >= cutoff_date
        ).order_by(desc(Incident.created_at)).limit(15).all()
        
        incident_data = [['Date', 'Title', 'Severity', 'Status', 'Department', 'Assigned To']]
        
        for incident in recent_incidents:
            assigned_name = incident.assigned_to.full_name if incident.assigned_to else 'Unassigned'
            incident_data.append([
                incident.created_at.strftime('%m/%d/%Y') if incident.created_at else 'N/A',
                incident.title[:30] + '...' if len(incident.title) > 30 else incident.title,
                incident.severity.value.upper() if incident.severity else 'N/A',
                incident.status.value.upper() if incident.status else 'N/A',
                incident.department or 'N/A',
                assigned_name[:15] + '...' if len(assigned_name) > 15 else assigned_name
            ])
        
        incident_table = Table(incident_data, colWidths=[0.8*inch, 2.2*inch, 0.8*inch, 0.8*inch, 1*inch, 1.2*inch])
        incident_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ]))
        
        return incident_table

    def _create_compliance_overview(self, db: Session) -> Table:
        """Create compliance overview - placeholder for now"""
        compliance_data = [
            ['Compliance Framework', 'Status', 'Compliance %', 'Last Review'],
            ['ISO 31000', 'ACTIVE', '85%', '2024-08-15'],
            ['ZPPA Guidelines', 'ACTIVE', '92%', '2024-08-20'],
            ['Internal Policies', 'ACTIVE', '78%', '2024-08-10'],
            ['BOZ Regulations', 'ACTIVE', '88%', '2024-08-18']
        ]
        
        compliance_table = Table(compliance_data, colWidths=[2.5*inch, 1*inch, 1*inch, 1.2*inch])
        compliance_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ]))
        
        return compliance_table

    def generate_risk_assessment_report(self, db: Session, user_name: str, assessment_id: Optional[str] = None) -> bytes:
        """Generate detailed risk assessment report"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Header
        story.append(self._create_header("Risk Assessment Report", user_name))
        story.append(Spacer(1, 0.3*inch))
        
        if assessment_id:
            # Specific assessment report
            assessment = db.query(RiskAssessment).filter(RiskAssessment.id == assessment_id).first()
            if assessment:
                story.append(self._create_specific_assessment_content(assessment))
        else:
            # General assessment overview
            story.append(self._create_general_assessment_overview(db))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.read()

    def _create_specific_assessment_content(self, assessment: RiskAssessment) -> List:
        """Create content for specific risk assessment"""
        content = []
        
        content.append(Paragraph(f"Assessment Details for: {assessment.risk.title}", self.subtitle_style))
        
        assessment_data = [
            ['Assessment Field', 'Value'],
            ['Risk Title', assessment.risk.title],
            ['Assessment Date', assessment.assessment_date.strftime('%Y-%m-%d')],
            ['Assessor', assessment.assessor_name or 'N/A'],
            ['Likelihood', str(assessment.likelihood)],
            ['Impact', str(assessment.impact)],
            ['Risk Score', str(assessment.residual_risk_score or 0)],
            ['Notes', assessment.notes[:100] + '...' if assessment.notes and len(assessment.notes) > 100 else (assessment.notes or 'N/A')]
        ]
        
        assessment_table = Table(assessment_data, colWidths=[2*inch, 4*inch])
        assessment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        
        content.append(assessment_table)
        return content

    def _create_general_assessment_overview(self, db: Session) -> List:
        """Create general assessment overview"""
        content = []
        
        # Get recent assessments
        recent_assessments = db.query(RiskAssessment).order_by(
            desc(RiskAssessment.assessment_date)
        ).limit(20).all()
        
        content.append(Paragraph("Recent Risk Assessments", self.subtitle_style))
        
        assessment_data = [['Date', 'Risk Title', 'Assessor', 'Score', 'Status']]
        
        for assessment in recent_assessments:
            assessment_data.append([
                assessment.assessment_date.strftime('%Y-%m-%d'),
                assessment.risk.title[:40] + '...' if len(assessment.risk.title) > 40 else assessment.risk.title,
                assessment.assessor_name or 'N/A',
                str(assessment.residual_risk_score or 0),
                assessment.risk.status.value if assessment.risk.status else 'N/A'
            ])
        
        assessment_table = Table(assessment_data, colWidths=[0.8*inch, 2.8*inch, 1.2*inch, 0.6*inch, 0.8*inch])
        assessment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        
        content.append(assessment_table)
        return content

# Global instance
advanced_report_service = AdvancedReportService()