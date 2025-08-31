from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from io import BytesIO, StringIO
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import csv
import json

# Excel generation
try:
    import xlsxwriter
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

# PDF generation - using existing report service or fallback
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.control import Control
from app.models.compliance import ComplianceRequirement, ComplianceMapping, ComplianceAssessment
from app.services.reports import report_service
from app.models.risk import Risk
from app.models.assessment import RiskAssessment
from app.models.control import RiskControl
from app.models.workflow import RiskTreatment

router = APIRouter()

@router.get("/risk-report")
def generate_risk_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    ):
    """Generate PDF risk report"""
    pdf_bytes = report_service.generate_risk_report(db, current_user.full_name)
    
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=risk_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        }
    )

@router.get("/kri-report")
def generate_kri_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    ):
    """Generate PDF KRI report"""
    pdf_bytes = report_service.generate_kri_report(db)
    
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=kri_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        }
    )

@router.get("/risk-register", response_model=Dict[str, Any])
def generate_risk_register_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    format: str = Query("json", pattern="^(json|csv|pdf)$")
    ) -> Dict[str, Any]:
    """Generate comprehensive risk register report"""
    risks = db.query(Risk).all()
    
    risk_register = []
    for risk in risks:
        # Get latest assessment
        latest_assessment = db.query(RiskAssessment)\
            .filter(RiskAssessment.risk_id == risk.id)\
            .order_by(RiskAssessment.assessment_date.desc())\
            .first()
        
        # Get controls
        risk_controls = db.query(RiskControl)\
            .join(Control)\
            .filter(RiskControl.risk_id == risk.id)\
            .all()
        
        # Get treatment
        treatment = db.query(RiskTreatment)\
            .filter(RiskTreatment.risk_id == risk.id)\
            .order_by(RiskTreatment.created_at.desc())\
            .first()
        
        risk_entry = {
            "risk_id": str(risk.id),
            "title": risk.title,
            "description": risk.description,
            "category": risk.category.value if risk.category else None,
            "department": risk.department,
            "owner": risk.owner.full_name if risk.owner else None,
            "status": risk.status.value if risk.status else None,
            "inherent_risk": {
                "likelihood": risk.likelihood,
                "impact": risk.impact,
                "score": (risk.likelihood or 0) * (risk.impact or 0)
            },
            "residual_risk": {
                "likelihood": latest_assessment.likelihood if latest_assessment else risk.likelihood,
                "impact": latest_assessment.impact if latest_assessment else risk.impact,
                "score": (latest_assessment.likelihood * latest_assessment.impact) if latest_assessment else ((risk.likelihood or 0) * (risk.impact or 0))
            },
            "controls": [
                {
                    "name": rc.control.name,
                    "type": rc.control.control_type.value if rc.control.control_type else None,
                    "effectiveness": rc.control.effectiveness
                } for rc in risk_controls
            ],
            "treatment": {
                "strategy": treatment.strategy.value if treatment and treatment.strategy else None,
                "status": treatment.status.value if treatment and treatment.status else None,
                "target_date": treatment.target_date.isoformat() if treatment and treatment.target_date else None
            } if treatment else None,
            "last_assessed": latest_assessment.assessment_date.isoformat() if latest_assessment else None,
            "created_date": risk.created_at.isoformat(),
            "updated_date": risk.updated_at.isoformat()
        }
        
        risk_register.append(risk_entry)
    
    # Sort by risk score (descending)
    risk_register.sort(key=lambda x: x["residual_risk"]["score"], reverse=True)
    
    report = {
        "title": "Risk Register Report",
        "generated_date": datetime.now(timezone.utc).isoformat(),
        "generated_by": current_user.full_name,
        "total_risks": len(risk_register),
        "summary": {
            "very_high": len([r for r in risk_register if r["residual_risk"]["score"] >= 20]),
            "high": len([r for r in risk_register if 15 <= r["residual_risk"]["score"] < 20]),
            "medium": len([r for r in risk_register if 10 <= r["residual_risk"]["score"] < 15]),
            "low": len([r for r in risk_register if 5 <= r["residual_risk"]["score"] < 10]),
            "very_low": len([r for r in risk_register if r["residual_risk"]["score"] < 5])
        },
        "risks": risk_register
    }
    
    if format == "csv":
        # Convert to CSV format
        output = StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            "Risk ID", "Title", "Category", "Department", "Owner",
            "Inherent Likelihood", "Inherent Impact", "Inherent Score",
            "Residual Likelihood", "Residual Impact", "Residual Score",
            "Controls Count", "Treatment Strategy", "Status", "Last Assessed"
        ])
        
        # Write data
        for risk in risk_register:
            writer.writerow([
                risk["risk_id"],
                risk["title"],
                risk["category"],
                risk["department"],
                risk["owner"],
                risk["inherent_risk"]["likelihood"],
                risk["inherent_risk"]["impact"],
                risk["inherent_risk"]["score"],
                risk["residual_risk"]["likelihood"],
                risk["residual_risk"]["impact"],
                risk["residual_risk"]["score"],
                len(risk["controls"]),
                risk["treatment"]["strategy"] if risk["treatment"] else "",
                risk["status"],
                risk["last_assessed"]
            ])
        
        return {
            "format": "csv",
            "content": output.getvalue(),
            "filename": f"risk_register_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    
    return report

@router.get("/compliance", response_model=Dict[str, Any])
def generate_compliance_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    framework: Optional[str] = Query(None)
    ) -> Dict[str, Any]:
    """Generate compliance status report"""
    query = db.query(ComplianceRequirement)
    if framework:
        query = query.filter(ComplianceRequirement.framework == framework)
    
    requirements = query.all()
    mappings = db.query(ComplianceMapping).all()
    assessments = db.query(ComplianceAssessment).all()
    
    # Build compliance report
    compliance_data = {}
    
    for req in requirements:
        if req.framework not in compliance_data:
            compliance_data[req.framework] = {
                "framework_name": req.framework,
                "total_requirements": 0,
                "mapped_requirements": 0,
                "compliance_percentage": 0,
                "requirements": [],
                "gap_summary": {
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0
                }
            }
        
        framework_data = compliance_data[req.framework]
        framework_data["total_requirements"] += 1
        
        # Check if requirement is mapped
        req_mappings = [m for m in mappings if m.requirement_id == req.id]
        is_mapped = len(req_mappings) > 0
        
        if is_mapped:
            framework_data["mapped_requirements"] += 1
        
        requirement_detail = {
            "requirement_id": req.requirement_id,
            "title": req.title,
            "description": req.description,
            "category": req.category if hasattr(req, 'category') else None,
            "is_mapped": is_mapped,
            "mapped_controls": [
                {
                    "control_id": str(m.control_id),
                    "implementation_status": m.implementation_status.value if hasattr(m.implementation_status, 'value') else m.implementation_status
                } for m in req_mappings
            ] if is_mapped else [],
            "compliance_status": "compliant" if is_mapped else "non_compliant"
        }
        
        framework_data["requirements"].append(requirement_detail)
        
        # Update gap summary
        if not is_mapped:
            priority = getattr(req, 'priority', 'medium')
            if priority in framework_data["gap_summary"]:
                framework_data["gap_summary"][priority] += 1
    
    # Calculate compliance percentages
    for framework, data in compliance_data.items():
        if data["total_requirements"] > 0:
            data["compliance_percentage"] = round(
                (data["mapped_requirements"] / data["total_requirements"]) * 100, 2
            )
    
    # Get recent assessments
    recent_assessments = sorted(assessments, key=lambda a: a.assessment_date, reverse=True)[:10]
    
    report = {
        "title": "Compliance Status Report",
        "generated_date": datetime.now(timezone.utc).isoformat(),
        "generated_by": current_user.full_name,
        "frameworks": list(compliance_data.values()),
        "overall_compliance": round(
            sum(f["compliance_percentage"] for f in compliance_data.values()) / len(compliance_data), 2
        ) if compliance_data else 0,
        "recent_assessments": [
            {
                "id": str(a.id),
                "framework": a.framework,
                "assessment_date": a.assessment_date.isoformat(),
                "compliance_score": a.compliance_score,
                "gaps_identified": a.gaps_identified if hasattr(a, 'gaps_identified') else 0
            } for a in recent_assessments
        ],
        "total_gaps": sum(
            f["total_requirements"] - f["mapped_requirements"] 
            for f in compliance_data.values()
        )
    }
    
    return report

# Excel Export Functions
def generate_excel_report(sheets_data: Dict[str, Dict]) -> BytesIO:
    """Generate Excel report with multiple sheets"""
    if not EXCEL_AVAILABLE:
        raise ImportError("xlsxwriter not installed. Install with: pip install xlsxwriter")
    
    buffer = BytesIO()
    workbook = xlsxwriter.Workbook(buffer)
    
    # Define formats
    header_format = workbook.add_format({
        "bold": True,
        "bg_color": "#1e4d8b",
        "font_color": "white",
        "border": 1,
        "align": "center"
    })
    
    data_format = workbook.add_format({"border": 1})
    date_format = workbook.add_format({"border": 1, "num_format": "yyyy-mm-dd"})
    
    # Create sheets
    for sheet_name, sheet_info in sheets_data.items():
        worksheet = workbook.add_worksheet(sheet_name[:31])  # Excel sheet name limit
        
        # Write headers
        headers = sheet_info.get("headers", [])
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Write data
        data = sheet_info.get("data", [])
        for row_idx, row_data in enumerate(data, start=1):
            for col_idx, value in enumerate(row_data):
                if isinstance(value, datetime):
                    worksheet.write(row_idx, col_idx, value, date_format)
                else:
                    worksheet.write(row_idx, col_idx, value, data_format)
        
        # Auto-fit columns
        for col in range(len(headers)):
            worksheet.set_column(col, col, 15)
    
    workbook.close()
    buffer.seek(0)
    return buffer

@router.get("/export/risk-register")
async def export_risk_register(
    format: str = Query("excel", pattern="^(excel|csv)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export Risk Register to Excel or CSV"""
    
    # Get all risks with related data
    risks = db.query(Risk).all()
    
    if format == "csv":
        # CSV export
        output = StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow(["Risk ID", "Title", "Description", "Category", "Status", 
                        "Likelihood", "Impact", "Inherent Score", "Residual Score", 
                        "Owner", "Created Date", "Last Updated"])
        
        # Data rows
        for risk in risks:
            owner_name = "Unassigned"
            if risk.risk_owner_id:
                owner = db.query(User).filter(User.id == risk.risk_owner_id).first()
                if owner:
                    owner_name = owner.full_name
            
            writer.writerow([
                str(risk.id),
                risk.title,
                risk.description[:200] if risk.description else "",
                risk.category.value if risk.category else "",
                risk.status.value if risk.status else "",
                risk.likelihood,
                risk.impact,
                risk.inherent_risk_score,
                risk.residual_risk_score or "",
                owner_name,
                risk.created_at.strftime("%Y-%m-%d") if risk.created_at else "",
                risk.updated_at.strftime("%Y-%m-%d") if risk.updated_at else ""
            ])
        
        output.seek(0)
        filename = f"risk_register_{datetime.now().strftime('%Y%m%d')}.csv"
        return StreamingResponse(
            StringIO(output.getvalue()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    else:  # Excel format
        # Prepare data for Excel
        risk_data = []
        for risk in risks:
            owner_name = "Unassigned"
            if risk.risk_owner_id:
                owner = db.query(User).filter(User.id == risk.risk_owner_id).first()
                if owner:
                    owner_name = owner.full_name
            
            risk_data.append([
                str(risk.id)[:8],
                risk.title,
                risk.description[:200] if risk.description else "",
                risk.category.value if risk.category else "",
                risk.status.value if risk.status else "",
                risk.likelihood,
                risk.impact,
                risk.inherent_risk_score,
                risk.residual_risk_score or 0,
                owner_name,
                risk.created_at if risk.created_at else None,
                risk.updated_at if risk.updated_at else None
            ])
        
        sheets_data = {
            "Risk Register": {
                "headers": ["Risk ID", "Title", "Description", "Category", "Status", 
                           "Likelihood", "Impact", "Inherent Score", "Residual Score", 
                           "Owner", "Created Date", "Last Updated"],
                "data": risk_data
            }
        }
        
        buffer = generate_excel_report(sheets_data)
        filename = f"risk_register_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
