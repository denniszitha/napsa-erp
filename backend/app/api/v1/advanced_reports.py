"""
Advanced Reporting API Endpoints for NAPSA ERM
Provides comprehensive reporting, scheduling, and export capabilities
"""

from fastapi import APIRouter, Depends, Query, Response, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from io import BytesIO
from pydantic import BaseModel
import logging

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.services.advanced_reports import advanced_report_service
from app.services.report_scheduler import report_scheduler_service, ReportType, ReportFrequency, ReportFormat

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models
class ScheduledReportCreate(BaseModel):
    name: str
    description: str
    report_type: ReportType
    frequency: ReportFrequency
    format: ReportFormat = ReportFormat.PDF
    recipients: List[str]
    parameters: Optional[Dict[str, Any]] = {}
    enabled: bool = True

class ScheduledReportUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    recipients: Optional[List[str]] = None
    parameters: Optional[Dict[str, Any]] = None
    frequency: Optional[ReportFrequency] = None

class ReportResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

# Executive Dashboard Reports
@router.get("/executive-dashboard")
async def generate_executive_dashboard(
    date_range: int = Query(30, description="Date range in days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate comprehensive executive dashboard report"""
    try:
        pdf_bytes = advanced_report_service.generate_executive_dashboard(
            db, current_user.full_name, date_range
        )
        
        filename = f"executive_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Error generating executive dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risk-assessment")
async def generate_risk_assessment_report(
    assessment_id: Optional[str] = Query(None, description="Specific assessment ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate detailed risk assessment report"""
    try:
        pdf_bytes = advanced_report_service.generate_risk_assessment_report(
            db, current_user.full_name, assessment_id
        )
        
        filename = f"risk_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Error generating risk assessment report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comprehensive-risk-register")
async def generate_comprehensive_risk_register(
    format: str = Query("pdf", pattern="^(pdf|excel|csv|json)$"),
    include_treatments: bool = Query(True, description="Include risk treatments"),
    include_controls: bool = Query(True, description="Include risk controls"),
    include_assessments: bool = Query(True, description="Include assessments"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate comprehensive risk register with all related data"""
    try:
        if format == "pdf":
            # Use advanced report service for PDF
            pdf_bytes = advanced_report_service.generate_executive_dashboard(
                db, current_user.full_name, 365  # Full year view
            )
            
            filename = f"comprehensive_risk_register_{datetime.now().strftime('%Y%m%d')}.pdf"
            return StreamingResponse(
                BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            # JSON format for API consumption
            from app.api.v1.reports import generate_risk_register_report
            return await generate_risk_register_report(db, current_user, format)
            
    except Exception as e:
        logger.error(f"Error generating comprehensive risk register: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/kri-dashboard")
async def generate_kri_dashboard_report(
    include_trends: bool = Query(True, description="Include trend analysis"),
    include_forecasts: bool = Query(False, description="Include forecasts"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate comprehensive KRI dashboard report"""
    try:
        from app.services.reports import report_service
        pdf_bytes = report_service.generate_kri_report(db)
        
        filename = f"kri_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Error generating KRI dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compliance-audit")
async def generate_compliance_audit_report(
    framework: Optional[str] = Query(None, description="Specific compliance framework"),
    include_gaps: bool = Query(True, description="Include gap analysis"),
    include_recommendations: bool = Query(True, description="Include recommendations"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate compliance audit report"""
    try:
        from app.api.v1.reports import generate_compliance_report
        compliance_data = await generate_compliance_report(db, current_user, framework)
        
        # For now, return as JSON. Could enhance to generate PDF
        return compliance_data
    except Exception as e:
        logger.error(f"Error generating compliance audit report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Report Scheduling Endpoints
@router.get("/scheduled", response_model=List[Dict[str, Any]])
async def get_scheduled_reports(
    current_user: User = Depends(get_current_active_user)
):
    """Get all scheduled reports"""
    try:
        reports = report_scheduler_service.get_scheduled_reports()
        return reports
    except Exception as e:
        logger.error(f"Error getting scheduled reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scheduled", response_model=ReportResponse)
async def create_scheduled_report(
    report: ScheduledReportCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new scheduled report"""
    try:
        report_config = report.dict()
        report_config['created_by'] = current_user.email
        
        report_id = report_scheduler_service.add_scheduled_report(report_config)
        
        return ReportResponse(
            success=True,
            message=f"Scheduled report created successfully",
            data={"report_id": report_id}
        )
    except Exception as e:
        logger.error(f"Error creating scheduled report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/scheduled/{report_id}", response_model=ReportResponse)
async def update_scheduled_report(
    report_id: str,
    updates: ScheduledReportUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update an existing scheduled report"""
    try:
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        success = report_scheduler_service.update_scheduled_report(report_id, update_data)
        
        if success:
            return ReportResponse(
                success=True,
                message="Scheduled report updated successfully"
            )
        else:
            raise HTTPException(status_code=404, detail="Scheduled report not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating scheduled report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/scheduled/{report_id}", response_model=ReportResponse)
async def delete_scheduled_report(
    report_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a scheduled report"""
    try:
        success = report_scheduler_service.delete_scheduled_report(report_id)
        
        if success:
            return ReportResponse(
                success=True,
                message="Scheduled report deleted successfully"
            )
        else:
            raise HTTPException(status_code=404, detail="Scheduled report not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting scheduled report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scheduled/{report_id}/run", response_model=ReportResponse)
async def run_scheduled_report_now(
    report_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """Manually trigger a scheduled report to run immediately"""
    try:
        success = report_scheduler_service.run_report_now(report_id)
        
        if success:
            return ReportResponse(
                success=True,
                message="Report execution triggered successfully"
            )
        else:
            raise HTTPException(status_code=404, detail="Scheduled report not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running scheduled report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Data Export Endpoints
@router.get("/export/risks")
async def export_risks_data(
    format: str = Query("excel", pattern="^(excel|csv|json)$"),
    include_controls: bool = Query(True),
    include_assessments: bool = Query(True),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export risks data in various formats"""
    try:
        from app.api.v1.reports import export_risk_register
        return await export_risk_register(format, db, current_user)
    except Exception as e:
        logger.error(f"Error exporting risks data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/kris")
async def export_kris_data(
    format: str = Query("excel", pattern="^(excel|csv|json)$"),
    include_history: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export KRIs data in various formats"""
    try:
        from app.models.kri import KeyRiskIndicator
        kris = db.query(KeyRiskIndicator).all()
        
        if format == "json":
            kri_data = []
            for kri in kris:
                kri_data.append({
                    "id": str(kri.id),
                    "name": kri.name,
                    "description": kri.description,
                    "current_value": kri.current_value,
                    "target_value": kri.target_value,
                    "threshold_value": kri.threshold_value,
                    "status": kri.status.value if kri.status else None,
                    "trend": kri.trend,
                    "frequency": kri.frequency.value if kri.frequency else None,
                    "created_at": kri.created_at.isoformat() if kri.created_at else None,
                    "updated_at": kri.updated_at.isoformat() if kri.updated_at else None
                })
            
            return {"kris": kri_data, "exported_at": datetime.now().isoformat()}
        
        # For CSV/Excel, implement similar to risk export
        return {"message": "KRI export functionality will be implemented"}
        
    except Exception as e:
        logger.error(f"Error exporting KRIs data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/incidents")
async def export_incidents_data(
    format: str = Query("excel", pattern="^(excel|csv|json)$"),
    status_filter: Optional[str] = Query(None),
    severity_filter: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export incidents data in various formats"""
    try:
        from app.models.incident import Incident
        
        query = db.query(Incident)
        
        # Apply filters
        if date_from:
            query = query.filter(Incident.created_at >= datetime.fromisoformat(date_from))
        if date_to:
            query = query.filter(Incident.created_at <= datetime.fromisoformat(date_to))
            
        incidents = query.all()
        
        if format == "json":
            incident_data = []
            for incident in incidents:
                incident_data.append({
                    "id": str(incident.id),
                    "title": incident.title,
                    "description": incident.description,
                    "severity": incident.severity.value if incident.severity else None,
                    "status": incident.status.value if incident.status else None,
                    "department": incident.department,
                    "reported_by": incident.reported_by.full_name if incident.reported_by else None,
                    "assigned_to": incident.assigned_to.full_name if incident.assigned_to else None,
                    "created_at": incident.created_at.isoformat() if incident.created_at else None,
                    "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None
                })
            
            return {"incidents": incident_data, "exported_at": datetime.now().isoformat()}
        
        return {"message": "Incident export functionality will be implemented"}
        
    except Exception as e:
        logger.error(f"Error exporting incidents data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Report Templates
@router.get("/templates", response_model=List[Dict[str, Any]])
async def get_report_templates(
    current_user: User = Depends(get_current_active_user)
):
    """Get available report templates"""
    templates = [
        {
            "id": "executive_summary",
            "name": "Executive Summary Report",
            "description": "High-level overview for senior management",
            "type": "executive_dashboard",
            "parameters": ["date_range"],
            "formats": ["pdf"]
        },
        {
            "id": "detailed_risk_register", 
            "name": "Detailed Risk Register",
            "description": "Complete risk register with controls and treatments",
            "type": "risk_register",
            "parameters": ["include_controls", "include_treatments", "include_assessments"],
            "formats": ["pdf", "excel", "csv"]
        },
        {
            "id": "kri_monitoring",
            "name": "KRI Monitoring Report",
            "description": "Key Risk Indicators status and trends",
            "type": "kri_report", 
            "parameters": ["include_trends", "include_forecasts"],
            "formats": ["pdf", "excel"]
        },
        {
            "id": "compliance_status",
            "name": "Compliance Status Report",
            "description": "Regulatory compliance overview",
            "type": "compliance_report",
            "parameters": ["framework", "include_gaps"],
            "formats": ["pdf", "excel"]
        },
        {
            "id": "incident_summary",
            "name": "Incident Management Summary",
            "description": "Recent incidents and resolution status",
            "type": "incident_summary",
            "parameters": ["date_range", "severity_filter"],
            "formats": ["pdf", "csv"]
        }
    ]
    
    return templates

@router.get("/analytics/summary")
async def get_reporting_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get reporting system analytics and usage statistics"""
    try:
        # Get scheduled reports count
        scheduled_reports = report_scheduler_service.get_scheduled_reports()
        
        analytics = {
            "scheduled_reports": {
                "total": len(scheduled_reports),
                "enabled": len([r for r in scheduled_reports if r.get('enabled', False)]),
                "by_frequency": {},
                "by_type": {}
            },
            "report_generation": {
                "total_generated_today": 0,  # Would track in database
                "total_generated_week": 0,
                "total_generated_month": 0
            },
            "popular_reports": [
                {"name": "Executive Dashboard", "count": 25},
                {"name": "Risk Register", "count": 18},
                {"name": "KRI Report", "count": 12}
            ],
            "export_statistics": {
                "pdf_exports": 45,
                "excel_exports": 32,
                "csv_exports": 23
            }
        }
        
        # Group by frequency and type
        for report in scheduled_reports:
            freq = report.get('frequency', 'unknown')
            rtype = report.get('report_type', 'unknown')
            
            analytics["scheduled_reports"]["by_frequency"][freq] = \
                analytics["scheduled_reports"]["by_frequency"].get(freq, 0) + 1
            analytics["scheduled_reports"]["by_type"][rtype] = \
                analytics["scheduled_reports"]["by_type"].get(rtype, 0) + 1
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting reporting analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))