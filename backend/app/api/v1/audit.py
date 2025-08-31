from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.audit import AuditLog
from app.services.audit import audit_service
from typing import Dict, Any, List, Optional
from app.models.risk import Risk
from app.models.control import Control
from fastapi import Query

router = APIRouter()

@router.get("/")
def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    action: Optional[str] = None,
    days: Optional[int] = Query(None, description="Filter logs from last N days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get audit logs"""
    if current_user.role not in ["admin", "auditor"]:
        raise HTTPException(status_code=403, detail="Not authorized to view audit logs")
    
    query = db.query(AuditLog)
    
    # Apply filters
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if days:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        query = query.filter(AuditLog.timestamp >= since)
    
    total = query.count()
    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "logs": [
            {
                "id": str(log.id),
                "timestamp": log.timestamp.isoformat(),
                "user_email": log.user_email,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_name": log.entity_name,
                "description": log.description,
                "ip_address": log.ip_address
            }
            for log in logs
        ]
    }

@router.get("/entity/{entity_type}/{entity_id}")
def get_entity_history(
    entity_type: str,
    entity_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get audit history for specific entity"""
    history = audit_service.get_entity_history(db, entity_type, str(entity_id))
    
    return {
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "history": [
            {
                "timestamp": log.timestamp.isoformat(),
                "user_email": log.user_email,
                "action": log.action,
                "description": log.description,
                "old_values": log.old_values,
                "new_values": log.new_values
            }
            for log in history
        ]
    }

@router.get("/logs", response_model=Dict[str, Any])
def get_audit_logs_detailed(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """Get detailed audit logs with filtering"""
    query = db.query(AuditLog)
    
    # Apply filters
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    logs = query.order_by(AuditLog.timestamp.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    # Group by action type
    action_summary = {}
    all_logs = query.all()
    for log in all_logs:
        if log.action not in action_summary:
            action_summary[log.action] = 0
        action_summary[log.action] += 1
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "logs": [
            {
                "id": str(log.id),
                "timestamp": log.timestamp.isoformat(),
                "user": log.user.full_name if log.user else "System",
                "user_id": str(log.user_id) if log.user_id else None,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": log.details,
                "ip_address": log.ip_address if hasattr(log, 'ip_address') else None
            } for log in logs
        ],
        "action_summary": action_summary,
        "filters_applied": {
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        }
    }

@router.get("/user-activities", response_model=Dict[str, Any])
def get_user_activities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    user_id: Optional[str] = None,
    days: int = Query(30, description="Number of days to analyze")
) -> Dict[str, Any]:
    """Get user activity summary"""
    target_user_id = user_id if user_id else str(current_user.id)
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Get user
    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's audit logs
    logs = db.query(AuditLog)\
        .filter(AuditLog.user_id == target_user_id)\
        .filter(AuditLog.timestamp >= cutoff_date)\
        .all()
    
    # Analyze activities
    activities = {
        "user": {
            "id": str(user.id),
            "name": user.full_name,
            "role": user.role.value if user.role else None,
            "department": user.department
        },
        "period_days": days,
        "total_activities": len(logs),
        "activities_by_type": {},
        "activities_by_resource": {},
        "daily_activity": {},
        "most_active_hours": {},
        "recent_activities": []
    }
    
    # Group by action type
    for log in logs:
        action = log.action
        if action not in activities["activities_by_type"]:
            activities["activities_by_type"][action] = 0
        activities["activities_by_type"][action] += 1
        
        # Group by resource type
        resource = log.resource_type
        if resource not in activities["activities_by_resource"]:
            activities["activities_by_resource"][resource] = 0
        activities["activities_by_resource"][resource] += 1
        
        # Daily activity
        date_key = log.timestamp.date().isoformat()
        if date_key not in activities["daily_activity"]:
            activities["daily_activity"][date_key] = 0
        activities["daily_activity"][date_key] += 1
        
        # Hour analysis
        hour = log.timestamp.hour
        if hour not in activities["most_active_hours"]:
            activities["most_active_hours"][hour] = 0
        activities["most_active_hours"][hour] += 1
    
    # Recent activities
    recent_logs = sorted(logs, key=lambda x: x.timestamp, reverse=True)[:10]
    activities["recent_activities"] = [
        {
            "timestamp": log.timestamp.isoformat(),
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details
        } for log in recent_logs
    ]
    
    return activities

@router.get("/changes", response_model=List[Dict[str, Any]])
def get_recent_changes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    days: int = Query(7, description="Number of days to look back"),
    resource_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get recent changes to system entities"""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Get audit logs for changes
    query = db.query(AuditLog)\
        .filter(AuditLog.timestamp >= cutoff_date)\
        .filter(AuditLog.action.in_(['created', 'updated', 'deleted', 'status_changed']))
    
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    
    changes = query.order_by(AuditLog.timestamp.desc()).all()
    
    # Format changes
    formatted_changes = []
    for change in changes:
        change_detail = {
            "id": str(change.id),
            "timestamp": change.timestamp.isoformat(),
            "user": change.user.full_name if change.user else "System",
            "action": change.action,
            "resource_type": change.resource_type,
            "resource_id": change.resource_id,
            "summary": f"{change.user.full_name if change.user else 'System'} {change.action} {change.resource_type}",
            "details": change.details
        }
        
        # Add resource-specific information
        if change.resource_type == "risk" and change.resource_id:
            risk = db.query(Risk).filter(Risk.id == change.resource_id).first()
            if risk:
                change_detail["resource_name"] = risk.title
                change_detail["resource_details"] = {
                    "category": risk.category.value if risk.category else None,
                    "status": risk.status.value if risk.status else None
                }
        elif change.resource_type == "control" and change.resource_id:
            control = db.query(Control).filter(Control.id == change.resource_id).first()
            if control:
                change_detail["resource_name"] = control.name
                change_detail["resource_details"] = {
                    "type": control.control_type.value if control.control_type else None,
                    "status": control.implementation_status.value if control.implementation_status else None
                }
        
        formatted_changes.append(change_detail)
    
    return formatted_changes
