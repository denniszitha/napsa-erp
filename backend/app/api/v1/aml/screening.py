from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.api.deps import get_db, get_current_active_user
from app.models.user import User

router = APIRouter()


@router.post("/sanctions/check")
def check_sanctions(
    name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Check a name against sanctions lists"""
    # Placeholder for sanctions screening
    return {"status": "clean", "matches": []}


@router.post("/watchlist/screen")
def screen_watchlist(
    entity: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Screen an entity against watchlists"""
    # Placeholder for watchlist screening
    return {"status": "no_match", "results": []}