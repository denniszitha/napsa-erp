"""
Regulatory Reporting API
Provides endpoints for automated regulatory report generation and management
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import io
import os

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.services.regulatory import (
    get_reporting_engine,
    ReportType,
    ReportFormat,
    ReportStatus
)

router = APIRouter()

# Pydantic models for API
class GenerateReportRequest(BaseModel):
    template_id: str
    period_start: datetime
    period_end: datetime
    parameters: Optional[Dict[str, Any]] = None

class ReportResponse(BaseModel):
    report_id: str
    template_name: str
    status: str
    generated_at: str
    record_count: int
    file_size: Optional[int] = None

class TemplateResponse(BaseModel):
    template_id: str
    name: str
    report_type: str
    description: str
    format: str
    frequency: str
    regulatory_authority: str

@router.post("/generate")
async def generate_report(
    request: GenerateReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate a regulatory report
    """
    try:
        reporting_engine = get_reporting_engine()
        
        # Validate template exists
        templates = reporting_engine.get_available_templates()
        template_ids = [t["template_id"] for t in templates]
        
        if request.template_id not in template_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Template not found. Available templates: {template_ids}"
            )
        
        # Validate date range
        if request.period_start >= request.period_end:
            raise HTTPException(
                status_code=400,
                detail="Period start must be before period end"
            )
        
        # Generate report in background
        def generate_report_background():
            try:
                report_id = reporting_engine.generate_report(
                    template_id=request.template_id,
                    period_start=request.period_start,
                    period_end=request.period_end,
                    generated_by=current_user.email,
                    db=db,
                    parameters=request.parameters
                )
                return report_id
            except Exception as e:
                logger.error(f"Background report generation failed: {e}")
        
        background_tasks.add_task(generate_report_background)
        
        return {
            "status": "accepted",
            "message": "Report generation started",
            "template_id": request.template_id,
            "estimated_completion": "2-5 minutes"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start report generation: {str(e)}")

@router.get("/reports/{report_id}/status")
async def get_report_status(
    report_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the status of a report generation
    """
    try:
        reporting_engine = get_reporting_engine()
        status = reporting_engine.get_report_status(report_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get report status: {str(e)}")

@router.get("/reports")
async def list_reports(
    status: Optional[str] = None,
    report_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user)
):
    """
    List generated reports with filters
    """
    try:
        reporting_engine = get_reporting_engine()
        
        # Get reports in date range
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)  # Default to last 30 days
        if not end_date:
            end_date = datetime.now()
        
        reports = reporting_engine.get_reports_by_period(start_date, end_date)
        
        # Apply filters
        if status:
            reports = [r for r in reports if r["status"] == status]
        
        if report_type:
            reports = [r for r in reports if r["report_type"] == report_type]
        
        # Apply limit
        reports = reports[:limit]
        
        return {
            "reports": reports,
            "total": len(reports),
            "filters": {
                "status": status,
                "report_type": report_type,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "limit": limit
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list reports: {str(e)}")

@router.get("/templates")
async def get_report_templates(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get available report templates
    """
    try:
        reporting_engine = get_reporting_engine()
        templates = reporting_engine.get_available_templates()
        
        return {
            "templates": templates,
            "total": len(templates)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")

@router.get("/templates/{template_id}")
async def get_template_details(
    template_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed information about a specific template
    """
    try:
        reporting_engine = get_reporting_engine()
        templates = reporting_engine.get_available_templates()
        
        template = next((t for t in templates if t["template_id"] == template_id), None)
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get template details: {str(e)}")

@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Download a generated report file
    """
    try:
        reporting_engine = get_reporting_engine()
        report_status = reporting_engine.get_report_status(report_id)
        
        if not report_status:
            raise HTTPException(status_code=404, detail="Report not found")
        
        if report_status["status"] != "completed":
            raise HTTPException(status_code=400, detail="Report is not ready for download")
        
        if not report_status["file_path"]:
            raise HTTPException(status_code=404, detail="Report file not found")
        
        # In a real implementation, this would serve the actual file
        # For now, we'll return a placeholder response
        return {
            "message": "File download would be implemented here",
            "file_path": report_status["file_path"],
            "file_size": report_status["file_size"],
            "content_type": "application/octet-stream"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download report: {str(e)}")

@router.get("/compliance/calendar")
async def get_compliance_calendar(
    year: int,
    month: Optional[int] = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get compliance reporting calendar for a specific period
    """
    try:
        reporting_engine = get_reporting_engine()
        calendar = reporting_engine.get_compliance_calendar(year, month)
        
        return calendar
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get compliance calendar: {str(e)}")

@router.get("/statistics")
async def get_reporting_statistics(
    period_days: int = 30,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get reporting statistics and metrics
    """
    try:
        reporting_engine = get_reporting_engine()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        reports = reporting_engine.get_reports_by_period(start_date, end_date)
        
        # Calculate statistics
        total_reports = len(reports)
        completed_reports = len([r for r in reports if r["status"] == "completed"])
        failed_reports = len([r for r in reports if r["status"] == "failed"])
        pending_reports = len([r for r in reports if r["status"] in ["pending", "generating"]])
        
        # Report type distribution
        type_distribution = {}
        for report in reports:
            report_type = report["report_type"]
            type_distribution[report_type] = type_distribution.get(report_type, 0) + 1
        
        # Template usage
        template_usage = {}
        for report in reports:
            template_id = report["template_id"]
            template_usage[template_id] = template_usage.get(template_id, 0) + 1
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": period_days
            },
            "summary": {
                "total_reports": total_reports,
                "completed_reports": completed_reports,
                "failed_reports": failed_reports,
                "pending_reports": pending_reports,
                "success_rate": round(completed_reports / total_reports * 100, 2) if total_reports > 0 else 0
            },
            "type_distribution": [
                {"type": k, "count": v, "percentage": round(v / total_reports * 100, 2)}
                for k, v in type_distribution.items()
            ],
            "template_usage": [
                {"template_id": k, "count": v, "percentage": round(v / total_reports * 100, 2)}
                for k, v in sorted(template_usage.items(), key=lambda x: x[1], reverse=True)
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get reporting statistics: {str(e)}")

@router.post("/reports/{report_id}/submit")
async def submit_report(
    report_id: str,
    submission_notes: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    Mark a report as submitted to regulatory authorities
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin privileges required for report submission")
    
    try:
        reporting_engine = get_reporting_engine()
        
        if report_id not in reporting_engine.generated_reports:
            raise HTTPException(status_code=404, detail="Report not found")
        
        report = reporting_engine.generated_reports[report_id]
        
        if report.status != ReportStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Only completed reports can be submitted")
        
        # Mark as submitted
        report.status = ReportStatus.SUBMITTED
        report.submitted_at = datetime.now()
        
        if submission_notes:
            if not report.metadata:
                report.metadata = {}
            report.metadata["submission_notes"] = submission_notes
            report.metadata["submitted_by"] = current_user.email
        
        return {
            "status": "success",
            "message": "Report marked as submitted",
            "submitted_at": report.submitted_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit report: {str(e)}")

@router.get("/report-types")
async def get_supported_report_types(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get supported report types and their descriptions
    """
    report_types = []
    for report_type in ReportType:
        description = {
            ReportType.SAR: "Suspicious Activity Report - Filed when suspicious activities are detected",
            ReportType.CTR: "Currency Transaction Report - Filed for cash transactions over $10,000",
            ReportType.FBAR: "Foreign Bank Account Report - Annual report of foreign financial accounts",
            ReportType.BSA: "Bank Secrecy Act Report - Various BSA compliance reports",
            ReportType.CDD: "Customer Due Diligence Report - Customer onboarding and ongoing monitoring",
            ReportType.EDD: "Enhanced Due Diligence Report - Higher risk customer assessments",
            ReportType.KYCRISK: "KYC Risk Assessment Report - Customer risk profiling and scoring",
            ReportType.SANCTIONS: "Sanctions Screening Report - OFAC and sanctions list screening results",
            ReportType.PEP: "Politically Exposed Persons Report - PEP identification and monitoring",
            ReportType.WIRE_TRANSFER: "Wire Transfer Report - International wire transfer reporting",
            ReportType.MONTHLY_COMPLIANCE: "Monthly Compliance Report - Internal compliance summary",
            ReportType.QUARTERLY_COMPLIANCE: "Quarterly Compliance Report - Quarterly compliance review",
            ReportType.ANNUAL_COMPLIANCE: "Annual Compliance Report - Annual compliance assessment"
        }.get(report_type, "Standard regulatory report")
        
        report_types.append({
            "type": report_type.value,
            "name": report_type.value.replace("_", " ").title(),
            "description": description
        })
    
    return {
        "report_types": report_types,
        "total_types": len(report_types)
    }

@router.get("/formats")
async def get_supported_formats(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get supported report formats
    """
    formats = []
    for format_type in ReportFormat:
        description = {
            ReportFormat.PDF: "Portable Document Format - Human-readable reports",
            ReportFormat.XML: "Extensible Markup Language - Structured data for regulatory systems",
            ReportFormat.CSV: "Comma-Separated Values - Tabular data format",
            ReportFormat.JSON: "JavaScript Object Notation - Structured data format",
            ReportFormat.EXCEL: "Microsoft Excel format - Spreadsheet with formatting"
        }.get(format_type, "Standard format")
        
        formats.append({
            "format": format_type.value,
            "name": format_type.value.upper(),
            "description": description,
            "mime_type": {
                ReportFormat.PDF: "application/pdf",
                ReportFormat.XML: "application/xml",
                ReportFormat.CSV: "text/csv",
                ReportFormat.JSON: "application/json",
                ReportFormat.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }.get(format_type, "application/octet-stream")
        })
    
    return {
        "formats": formats,
        "total_formats": len(formats)
    }

@router.get("/health")
async def reporting_health_check():
    """
    Health check for regulatory reporting service
    """
    try:
        reporting_engine = get_reporting_engine()
        
        # Check if engine is accessible
        templates = reporting_engine.get_available_templates()
        
        return {
            "status": "healthy",
            "available_templates": len(templates),
            "service": "regulatory_reporting",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "regulatory_reporting",
            "timestamp": datetime.now().isoformat()
        }