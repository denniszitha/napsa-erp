"""
Regulations Management API
Provides regulatory compliance and framework management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid

from app.api.deps import get_db
from app.models.regulation import Regulation
from app.schemas.regulation import RegulationCreate, RegulationUpdate

router = APIRouter()

@router.get("/")
async def get_regulations(
    framework: Optional[str] = Query(None, description="Filter by framework"),
    status: Optional[str] = Query(None, description="Filter by compliance status"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all regulations with filtering"""
    
    try:
        # Base query
        query = db.query(Regulation)
        
        # Apply filters
        if framework and framework != 'all':
            query = query.filter(Regulation.framework == framework)
        
        if status and status != 'all':
            query = query.filter(Regulation.compliance_status == status)
        
        if search:
            search_filter = or_(
                Regulation.title.ilike(f"%{search}%"),
                Regulation.description.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        regulations = query.offset(skip).limit(limit).all()
        
        # Convert to dict format
        regulations_data = []
        for reg in regulations:
            regulations_data.append({
                "id": str(reg.id),
                "title": reg.title,
                "framework": reg.framework,
                "description": reg.description,
                "compliance_status": reg.compliance_status,
                "last_updated": reg.updated_at.isoformat() if reg.updated_at else datetime.now().isoformat(),
                "requirements_count": reg.requirements_count or 0,
                "controls_mapped": reg.controls_mapped or 0,
                "effective_date": reg.effective_date.isoformat() if reg.effective_date else None,
                "next_review": reg.next_review.isoformat() if reg.next_review else None
            })
        
        # Calculate statistics
        stats = {
            "total": total,
            "compliant": len([r for r in regulations_data if r['compliance_status'] == 'compliant']),
            "partial": len([r for r in regulations_data if r['compliance_status'] == 'partial']),
            "non_compliant": len([r for r in regulations_data if r['compliance_status'] == 'non_compliant']),
            "frameworks": len(set(r['framework'] for r in regulations_data))
        }
        
        return {
            "success": True,
            "data": {
                "regulations": regulations_data,
                "total": total,
                "stats": stats
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching regulations: {str(e)}")

@router.get("/{regulation_id}")
async def get_regulation(
    regulation_id: str,
    db: Session = Depends(get_db)
):
    """Get specific regulation details"""
    
    try:
        regulation = db.query(Regulation).filter(Regulation.id == regulation_id).first()
        
        if not regulation:
            raise HTTPException(status_code=404, detail="Regulation not found")
        
        return {
            "success": True,
            "data": {
                "id": str(regulation.id),
                "title": regulation.title,
                "framework": regulation.framework,
                "description": regulation.description,
                "compliance_status": regulation.compliance_status,
                "requirements_count": regulation.requirements_count or 0,
                "controls_mapped": regulation.controls_mapped or 0,
                "effective_date": regulation.effective_date.isoformat() if regulation.effective_date else None,
                "next_review": regulation.next_review.isoformat() if regulation.next_review else None,
                "created_at": regulation.created_at.isoformat() if regulation.created_at else None,
                "updated_at": regulation.updated_at.isoformat() if regulation.updated_at else None,
                "created_by": regulation.created_by,
                "tags": regulation.tags or [],
                "regulatory_body": regulation.regulatory_body,
                "jurisdiction": regulation.jurisdiction
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching regulation: {str(e)}")

@router.post("/")
async def create_regulation(
    regulation: RegulationCreate,
    db: Session = Depends(get_db)
):
    """Create new regulation"""
    
    try:
        db_regulation = Regulation(
            id=uuid.uuid4(),
            title=regulation.title,
            framework=regulation.framework,
            description=regulation.description,
            compliance_status=regulation.compliance_status or "draft",
            regulatory_body=regulation.regulatory_body,
            jurisdiction=regulation.jurisdiction,
            effective_date=regulation.effective_date,
            next_review=regulation.next_review,
            requirements_count=regulation.requirements_count or 0,
            controls_mapped=0,
            tags=regulation.tags or [],
            created_by=regulation.created_by or "system",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(db_regulation)
        db.commit()
        db.refresh(db_regulation)
        
        return {
            "success": True,
            "data": {
                "id": str(db_regulation.id),
                "title": db_regulation.title,
                "framework": db_regulation.framework,
                "compliance_status": db_regulation.compliance_status
            },
            "message": "Regulation created successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating regulation: {str(e)}")

@router.put("/{regulation_id}")
async def update_regulation(
    regulation_id: str,
    regulation: RegulationUpdate,
    db: Session = Depends(get_db)
):
    """Update existing regulation"""
    
    try:
        db_regulation = db.query(Regulation).filter(Regulation.id == regulation_id).first()
        
        if not db_regulation:
            raise HTTPException(status_code=404, detail="Regulation not found")
        
        # Update fields
        if regulation.title is not None:
            db_regulation.title = regulation.title
        if regulation.description is not None:
            db_regulation.description = regulation.description
        if regulation.compliance_status is not None:
            db_regulation.compliance_status = regulation.compliance_status
        if regulation.regulatory_body is not None:
            db_regulation.regulatory_body = regulation.regulatory_body
        if regulation.jurisdiction is not None:
            db_regulation.jurisdiction = regulation.jurisdiction
        if regulation.effective_date is not None:
            db_regulation.effective_date = regulation.effective_date
        if regulation.next_review is not None:
            db_regulation.next_review = regulation.next_review
        if regulation.requirements_count is not None:
            db_regulation.requirements_count = regulation.requirements_count
        if regulation.tags is not None:
            db_regulation.tags = regulation.tags
        
        db_regulation.updated_at = datetime.now()
        
        db.commit()
        db.refresh(db_regulation)
        
        return {
            "success": True,
            "data": {
                "id": str(db_regulation.id),
                "title": db_regulation.title,
                "compliance_status": db_regulation.compliance_status
            },
            "message": "Regulation updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating regulation: {str(e)}")

@router.delete("/{regulation_id}")
async def delete_regulation(
    regulation_id: str,
    db: Session = Depends(get_db)
):
    """Delete regulation"""
    
    try:
        regulation = db.query(Regulation).filter(Regulation.id == regulation_id).first()
        
        if not regulation:
            raise HTTPException(status_code=404, detail="Regulation not found")
        
        db.delete(regulation)
        db.commit()
        
        return {
            "success": True,
            "message": "Regulation deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting regulation: {str(e)}")

@router.get("/stats/summary")
async def get_regulation_stats(
    db: Session = Depends(get_db)
):
    """Get regulation statistics"""
    
    try:
        total_regulations = db.query(Regulation).count()
        compliant = db.query(Regulation).filter(Regulation.compliance_status == 'compliant').count()
        partial = db.query(Regulation).filter(Regulation.compliance_status == 'partial').count()
        non_compliant = db.query(Regulation).filter(Regulation.compliance_status == 'non_compliant').count()
        
        # Get framework distribution
        frameworks = db.execute(text("""
            SELECT framework, COUNT(*) as count
            FROM regulations
            GROUP BY framework
            ORDER BY count DESC
        """)).fetchall()
        
        framework_stats = {fw.framework: fw.count for fw in frameworks}
        
        return {
            "success": True,
            "data": {
                "total_regulations": total_regulations,
                "compliant": compliant,
                "partial": partial,
                "non_compliant": non_compliant,
                "compliance_rate": round((compliant / total_regulations * 100) if total_regulations > 0 else 0, 1),
                "frameworks": framework_stats,
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")

@router.get("/compliance/status")
async def get_compliance_status(
    db: Session = Depends(get_db)
):
    """Get overall compliance status across all frameworks"""
    
    try:
        # Get compliance data from regulations table
        compliance_data = db.execute(text("""
            SELECT 
                framework,
                compliance_status,
                COUNT(*) as count,
                AVG(CASE 
                    WHEN compliance_status = 'compliant' THEN 100
                    WHEN compliance_status = 'partial' THEN 50
                    ELSE 0 
                END) as avg_score
            FROM regulations
            GROUP BY framework, compliance_status
        """)).fetchall()
        
        # Process data by framework
        frameworks = {}
        for row in compliance_data:
            if row.framework not in frameworks:
                frameworks[row.framework] = {
                    'compliant': 0,
                    'partial': 0,
                    'non_compliant': 0,
                    'total': 0,
                    'score': 0
                }
            
            frameworks[row.framework][row.compliance_status] = row.count
            frameworks[row.framework]['total'] += row.count
        
        # Calculate scores
        for framework in frameworks:
            fw_data = frameworks[framework]
            if fw_data['total'] > 0:
                fw_data['score'] = round(
                    ((fw_data['compliant'] * 100) + (fw_data['partial'] * 50)) / fw_data['total'],
                    1
                )
        
        # Calculate overall compliance
        total_regulations = sum(fw['total'] for fw in frameworks.values())
        total_compliant = sum(fw['compliant'] for fw in frameworks.values())
        total_partial = sum(fw['partial'] for fw in frameworks.values())
        
        overall_score = 0
        if total_regulations > 0:
            overall_score = round(
                ((total_compliant * 100) + (total_partial * 50)) / total_regulations,
                1
            )
        
        return {
            "success": True,
            "data": {
                "overall_compliance": overall_score,
                "frameworks": frameworks,
                "total_regulations": total_regulations,
                "trend": "improving" if overall_score > 75 else "stable",
                "last_assessment": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching compliance status: {str(e)}")

@router.get("/frameworks")
async def get_regulatory_frameworks(
    db: Session = Depends(get_db)
):
    """Get all regulatory frameworks"""
    
    try:
        frameworks = db.execute(text("""
            SELECT DISTINCT framework, COUNT(*) as regulation_count
            FROM regulations
            GROUP BY framework
            ORDER BY regulation_count DESC
        """)).fetchall()
        
        framework_list = []
        for fw in frameworks:
            framework_list.append({
                "name": fw.framework,
                "regulation_count": fw.regulation_count,
                "description": f"{fw.framework} regulatory framework"
            })
        
        return {
            "success": True,
            "data": {
                "frameworks": framework_list,
                "total": len(framework_list)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching frameworks: {str(e)}")