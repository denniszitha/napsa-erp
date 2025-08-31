"""
Report Generation API endpoints
Generates PDF and Excel reports for NAPSA requirements
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import io
import os
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import xlsxwriter

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.risk import Risk
from app.models.incident import Incident
from app.models.kri import KeyRiskIndicator
from app.models.control import Control
from app.models.rcsa import RCSAAssessment

router = APIRouter(prefix="/reports/generate", tags=["Report Generation"])

@router.get("/risk-register/pdf")
async def generate_risk_register_pdf(
    department_id: Optional[int] = None,
    category_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate PDF report for risk register"""
    
    # Query risks
    query = db.query(Risk)
    if department_id:
        query = query.filter(Risk.organizational_unit_id == department_id)
    if category_id:
        query = query.filter(Risk.category_id == category_id)
    if status:
        query = query.filter(Risk.status == status)
    
    risks = query.all()
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#003366'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    elements.append(Paragraph("NAPSA Risk Register Report", title_style))
    elements.append(Spacer(1, 12))
    
    # Report metadata
    elements.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Paragraph(f"Total Risks: {len(risks)}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Risk summary table
    data = [['Risk ID', 'Title', 'Category', 'Likelihood', 'Impact', 'Score', 'Status']]
    
    for risk in risks[:50]:  # Limit to 50 for PDF
        data.append([
            risk.id,
            risk.title[:30] + '...' if len(risk.title) > 30 else risk.title,
            risk.category or 'N/A',
            str(risk.likelihood or 'N/A'),
            str(risk.impact or 'N/A'),
            f"{risk.inherent_risk_score:.1f}" if risk.inherent_risk_score else 'N/A',
            risk.status
        ])
    
    # Create table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(table)
    
    # Risk statistics
    elements.append(PageBreak())
    elements.append(Paragraph("Risk Statistics", styles['Heading2']))
    
    high_risks = sum(1 for r in risks if (r.inherent_risk_score or 0) >= 15)
    medium_risks = sum(1 for r in risks if 8 <= (r.inherent_risk_score or 0) < 15)
    low_risks = sum(1 for r in risks if (r.inherent_risk_score or 0) < 8)
    
    stats_data = [
        ['Risk Level', 'Count', 'Percentage'],
        ['High (15-25)', str(high_risks), f"{(high_risks/len(risks)*100):.1f}%" if risks else "0%"],
        ['Medium (8-14)', str(medium_risks), f"{(medium_risks/len(risks)*100):.1f}%" if risks else "0%"],
        ['Low (1-7)', str(low_risks), f"{(low_risks/len(risks)*100):.1f}%" if risks else "0%"],
    ]
    
    stats_table = Table(stats_data)
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(stats_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=risk_register_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
        }
    )

@router.get("/risk-register/excel")
async def generate_risk_register_excel(
    department_id: Optional[int] = None,
    category_id: Optional[int] = None,
    include_treatments: bool = True,
    include_controls: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate Excel report for risk register with multiple sheets"""
    
    # Query risks
    query = db.query(Risk)
    if department_id:
        query = query.filter(Risk.organizational_unit_id == department_id)
    if category_id:
        query = query.filter(Risk.category_id == category_id)
    
    risks = query.all()
    
    # Create Excel file in memory
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    
    # Define formats
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#003366',
        'font_color': 'white',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    high_risk_format = workbook.add_format({'bg_color': '#ffcccc'})
    medium_risk_format = workbook.add_format({'bg_color': '#fff4cc'})
    low_risk_format = workbook.add_format({'bg_color': '#ccffcc'})
    
    # Sheet 1: Risk Register
    worksheet1 = workbook.add_worksheet('Risk Register')
    
    # Headers
    headers = ['Risk ID', 'Title', 'Description', 'Category', 'Department', 
               'Likelihood', 'Impact', 'Inherent Score', 'Residual Score', 
               'Status', 'Owner', 'Created Date', 'Last Updated']
    
    for col, header in enumerate(headers):
        worksheet1.write(0, col, header, header_format)
    
    # Data
    for row, risk in enumerate(risks, start=1):
        worksheet1.write(row, 0, risk.id)
        worksheet1.write(row, 1, risk.title)
        worksheet1.write(row, 2, risk.description or '')
        worksheet1.write(row, 3, risk.category or '')
        worksheet1.write(row, 4, risk.department or '')
        worksheet1.write(row, 5, risk.likelihood or 0)
        worksheet1.write(row, 6, risk.impact or 0)
        
        # Apply conditional formatting based on risk score
        inherent_score = risk.inherent_risk_score or 0
        worksheet1.write(row, 7, inherent_score)
        
        if inherent_score >= 15:
            worksheet1.set_row(row, None, high_risk_format)
        elif inherent_score >= 8:
            worksheet1.set_row(row, None, medium_risk_format)
        else:
            worksheet1.set_row(row, None, low_risk_format)
        
        worksheet1.write(row, 8, risk.residual_risk_score or 0)
        worksheet1.write(row, 9, risk.status)
        worksheet1.write(row, 10, risk.risk_owner_id or '')
        worksheet1.write(row, 11, risk.created_at.strftime('%Y-%m-%d') if risk.created_at else '')
        worksheet1.write(row, 12, risk.updated_at.strftime('%Y-%m-%d') if risk.updated_at else '')
    
    # Adjust column widths
    worksheet1.set_column('A:A', 15)  # Risk ID
    worksheet1.set_column('B:B', 30)  # Title
    worksheet1.set_column('C:C', 50)  # Description
    worksheet1.set_column('D:E', 20)  # Category, Department
    
    # Sheet 2: Risk Summary
    worksheet2 = workbook.add_worksheet('Risk Summary')
    
    # Summary statistics
    total_risks = len(risks)
    high_risks = sum(1 for r in risks if (r.inherent_risk_score or 0) >= 15)
    medium_risks = sum(1 for r in risks if 8 <= (r.inherent_risk_score or 0) < 15)
    low_risks = sum(1 for r in risks if (r.inherent_risk_score or 0) < 8)
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Risks', total_risks],
        ['High Risks (15-25)', high_risks],
        ['Medium Risks (8-14)', medium_risks],
        ['Low Risks (1-7)', low_risks],
        ['Average Inherent Score', sum((r.inherent_risk_score or 0) for r in risks) / total_risks if total_risks > 0 else 0],
        ['Average Residual Score', sum((r.residual_risk_score or 0) for r in risks) / total_risks if total_risks > 0 else 0],
    ]
    
    for row, data in enumerate(summary_data):
        for col, value in enumerate(data):
            if row == 0:
                worksheet2.write(row, col, value, header_format)
            else:
                worksheet2.write(row, col, value)
    
    # Sheet 3: Department Analysis
    worksheet3 = workbook.add_worksheet('Department Analysis')
    
    # Get department statistics
    dept_stats = db.query(
        Risk.department,
        func.count(Risk.id).label('count'),
        func.avg(Risk.inherent_risk_score).label('avg_score')
    ).group_by(Risk.department).all()
    
    dept_headers = ['Department', 'Risk Count', 'Average Score']
    for col, header in enumerate(dept_headers):
        worksheet3.write(0, col, header, header_format)
    
    for row, stat in enumerate(dept_stats, start=1):
        worksheet3.write(row, 0, stat.department or 'Unassigned')
        worksheet3.write(row, 1, stat.count)
        worksheet3.write(row, 2, float(stat.avg_score) if stat.avg_score else 0)
    
    # Add chart
    if len(dept_stats) > 0:
        chart = workbook.add_chart({'type': 'column'})
        chart.add_series({
            'categories': ['Department Analysis', 1, 0, len(dept_stats), 0],
            'values': ['Department Analysis', 1, 1, len(dept_stats), 1],
            'name': 'Risk Count by Department'
        })
        chart.set_title({'name': 'Risk Distribution by Department'})
        chart.set_x_axis({'name': 'Department'})
        chart.set_y_axis({'name': 'Number of Risks'})
        worksheet3.insert_chart('E2', chart, {'x_scale': 1.5, 'y_scale': 1.5})
    
    workbook.close()
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=risk_register_{datetime.utcnow().strftime('%Y%m%d')}.xlsx"
        }
    )

@router.get("/kri-report/pdf")
async def generate_kri_report_pdf(
    threshold_breached_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate PDF report for Key Risk Indicators"""
    
    query = db.query(KeyRiskIndicator)
    if threshold_breached_only:
        query = query.filter(
            or_(
                KeyRiskIndicator.current_value > KeyRiskIndicator.threshold_upper,
                KeyRiskIndicator.current_value < KeyRiskIndicator.threshold_lower
            )
        )
    
    kris = query.all()
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#003366'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    elements.append(Paragraph("NAPSA Key Risk Indicators Report", title_style))
    elements.append(Spacer(1, 12))
    
    # Report metadata
    elements.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Paragraph(f"Total KRIs: {len(kris)}", styles['Normal']))
    
    if threshold_breached_only:
        elements.append(Paragraph("Filter: Showing only KRIs with threshold breaches", styles['Normal']))
    
    elements.append(Spacer(1, 12))
    
    # KRI table
    data = [['KRI Name', 'Current Value', 'Target', 'Lower Threshold', 'Upper Threshold', 'Status']]
    
    for kri in kris[:30]:  # Limit for PDF
        status = 'Normal'
        if kri.current_value and kri.threshold_upper and kri.current_value > kri.threshold_upper:
            status = 'Above Threshold'
        elif kri.current_value and kri.threshold_lower and kri.current_value < kri.threshold_lower:
            status = 'Below Threshold'
        
        data.append([
            kri.name[:30] + '...' if len(kri.name) > 30 else kri.name,
            f"{kri.current_value:.2f}" if kri.current_value else 'N/A',
            f"{kri.target_value:.2f}" if kri.target_value else 'N/A',
            f"{kri.threshold_lower:.2f}" if kri.threshold_lower else 'N/A',
            f"{kri.threshold_upper:.2f}" if kri.threshold_upper else 'N/A',
            status
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=kri_report_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
        }
    )

@router.get("/incident-report/excel")
async def generate_incident_report_excel(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate Excel report for incidents"""
    
    query = db.query(Incident)
    
    if date_from:
        query = query.filter(Incident.created_at >= date_from)
    if date_to:
        query = query.filter(Incident.created_at <= date_to)
    if severity:
        query = query.filter(Incident.severity == severity)
    
    incidents = query.all()
    
    # Create Excel file
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    
    # Formats
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#003366',
        'font_color': 'white',
        'border': 1
    })
    
    critical_format = workbook.add_format({'bg_color': '#ff0000', 'font_color': 'white'})
    high_format = workbook.add_format({'bg_color': '#ff9900'})
    medium_format = workbook.add_format({'bg_color': '#ffff00'})
    low_format = workbook.add_format({'bg_color': '#00ff00'})
    
    # Incident Details Sheet
    worksheet = workbook.add_worksheet('Incident Report')
    
    headers = ['Incident ID', 'Title', 'Description', 'Severity', 'Priority', 
               'Status', 'Department', 'Reported By', 'Assigned To', 
               'Created Date', 'Resolution Date', 'Root Cause']
    
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
    
    for row, incident in enumerate(incidents, start=1):
        worksheet.write(row, 0, incident.id)
        worksheet.write(row, 1, incident.title)
        worksheet.write(row, 2, incident.description or '')
        
        # Apply severity formatting
        severity_val = incident.severity
        if severity_val == 'critical':
            worksheet.write(row, 3, severity_val, critical_format)
        elif severity_val == 'high':
            worksheet.write(row, 3, severity_val, high_format)
        elif severity_val == 'medium':
            worksheet.write(row, 3, severity_val, medium_format)
        else:
            worksheet.write(row, 3, severity_val, low_format)
        
        worksheet.write(row, 4, incident.priority or '')
        worksheet.write(row, 5, incident.status)
        worksheet.write(row, 6, incident.department or '')
        worksheet.write(row, 7, incident.reported_by or '')
        worksheet.write(row, 8, incident.assigned_to or '')
        worksheet.write(row, 9, incident.created_at.strftime('%Y-%m-%d %H:%M') if incident.created_at else '')
        worksheet.write(row, 10, incident.resolved_at.strftime('%Y-%m-%d %H:%M') if incident.resolved_at else '')
        worksheet.write(row, 11, incident.root_cause or '')
    
    # Adjust column widths
    worksheet.set_column('A:A', 15)
    worksheet.set_column('B:B', 30)
    worksheet.set_column('C:C', 50)
    worksheet.set_column('D:F', 15)
    
    # Summary Sheet
    summary_sheet = workbook.add_worksheet('Summary')
    
    total_incidents = len(incidents)
    critical_count = sum(1 for i in incidents if i.severity == 'critical')
    high_count = sum(1 for i in incidents if i.severity == 'high')
    resolved_count = sum(1 for i in incidents if i.status == 'resolved')
    
    summary_data = [
        ['Metric', 'Count'],
        ['Total Incidents', total_incidents],
        ['Critical Severity', critical_count],
        ['High Severity', high_count],
        ['Resolved', resolved_count],
        ['Open', total_incidents - resolved_count]
    ]
    
    for row, data in enumerate(summary_data):
        for col, value in enumerate(data):
            if row == 0:
                summary_sheet.write(row, col, value, header_format)
            else:
                summary_sheet.write(row, col, value)
    
    workbook.close()
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=incident_report_{datetime.utcnow().strftime('%Y%m%d')}.xlsx"
        }
    )

@router.get("/executive-summary/pdf")
async def generate_executive_summary_pdf(
    month: int = Query(default=datetime.utcnow().month),
    year: int = Query(default=datetime.utcnow().year),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate executive summary PDF report"""
    
    # Calculate date range
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    # Gather statistics
    total_risks = db.query(Risk).count()
    new_risks = db.query(Risk).filter(
        Risk.created_at >= start_date,
        Risk.created_at < end_date
    ).count()
    
    high_risks = db.query(Risk).filter(Risk.inherent_risk_score >= 15).count()
    
    total_incidents = db.query(Incident).filter(
        Incident.created_at >= start_date,
        Incident.created_at < end_date
    ).count()
    
    kri_breaches = db.query(KeyRiskIndicator).filter(
        or_(
            KeyRiskIndicator.current_value > KeyRiskIndicator.threshold_upper,
            KeyRiskIndicator.current_value < KeyRiskIndicator.threshold_lower
        )
    ).count()
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#003366'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    elements.append(Paragraph("NAPSA ERM Executive Summary", title_style))
    elements.append(Paragraph(f"{datetime(year, month, 1).strftime('%B %Y')}", styles['Heading2']))
    elements.append(Spacer(1, 20))
    
    # Key Metrics Section
    elements.append(Paragraph("Key Risk Metrics", styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    metrics_data = [
        ['Metric', 'Current Period', 'Status'],
        ['Total Active Risks', str(total_risks), '↑' if new_risks > 0 else '→'],
        ['New Risks This Month', str(new_risks), '-'],
        ['High Priority Risks', str(high_risks), '⚠' if high_risks > 10 else '✓'],
        ['Incidents Reported', str(total_incidents), '-'],
        ['KRI Threshold Breaches', str(kri_breaches), '⚠' if kri_breaches > 0 else '✓'],
    ]
    
    metrics_table = Table(metrics_data)
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(metrics_table)
    elements.append(Spacer(1, 20))
    
    # Risk Distribution
    elements.append(Paragraph("Risk Distribution by Category", styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    risk_dist = db.query(
        Risk.category,
        func.count(Risk.id).label('count')
    ).group_by(Risk.category).all()
    
    dist_data = [['Category', 'Count']]
    for item in risk_dist:
        dist_data.append([item.category or 'Uncategorized', str(item.count)])
    
    dist_table = Table(dist_data)
    dist_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(dist_table)
    
    # Recommendations
    elements.append(PageBreak())
    elements.append(Paragraph("Executive Recommendations", styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    recommendations = []
    if high_risks > 10:
        recommendations.append("• Immediate attention required for high-priority risks")
    if kri_breaches > 0:
        recommendations.append("• Review and address KRI threshold breaches")
    if new_risks > 5:
        recommendations.append("• Conduct detailed assessment of newly identified risks")
    if total_incidents > 10:
        recommendations.append("• Investigate root causes of incident trends")
    
    if not recommendations:
        recommendations.append("• Continue monitoring and maintain current risk management practices")
    
    for rec in recommendations:
        elements.append(Paragraph(rec, styles['Normal']))
        elements.append(Spacer(1, 6))
    
    # Footer
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(f"Report generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=executive_summary_{year}_{month:02d}.pdf"
        }
    )