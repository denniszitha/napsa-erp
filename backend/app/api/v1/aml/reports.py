from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db, get_current_active_user
from app.models.user import User

router = APIRouter()


@router.post("/sar")
def create_sar(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a Suspicious Activity Report"""
    # Placeholder for SAR creation
    return {"status": "created", "report_id": "SAR-001"}


@router.post("/ctr")
def create_ctr(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a Currency Transaction Report"""
    # Placeholder for CTR creation
    return {"status": "created", "report_id": "CTR-001"}


@router.get("/")
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all compliance reports"""
    return {"reports": []}