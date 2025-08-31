from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from io import BytesIO
from datetime import datetime
import json

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.services.data_exchange import data_exchange_service

router = APIRouter()

@router.get("/export/risks/excel")
def export_risks_excel(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Export all risks to Excel file"""
    excel_data = data_exchange_service.export_risks_to_excel(db)
    
    return StreamingResponse(
        BytesIO(excel_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=risks_export_{datetime.now().strftime('%Y%m%d')}.xlsx"
        }
    )

@router.get("/export/{entity_type}/csv")
def export_to_csv(
    entity_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Export data to CSV format"""
    if entity_type not in ["risks", "controls", "kris"]:
        raise HTTPException(status_code=400, detail="Invalid entity type")
    
    csv_data = data_exchange_service.export_to_csv(db, entity_type)
    
    return StreamingResponse(
        BytesIO(csv_data.encode()),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={entity_type}_export_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )

@router.post("/import/risks/csv")
async def import_risks_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Import risks from CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    contents = await file.read()
    csv_content = contents.decode('utf-8')
    
    result = data_exchange_service.import_risks_from_csv(
        db, csv_content, str(current_user.id)
    )
    
    return result

@router.get("/backup/full")
def export_full_backup(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Export full system backup as JSON"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create backups")
    
    backup_data = data_exchange_service.export_full_backup(db)
    
    return StreamingResponse(
        BytesIO(json.dumps(backup_data, indent=2).encode()),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=erm_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }
    )
