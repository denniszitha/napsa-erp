"""
Blockchain Audit API
Provides endpoints for blockchain-based audit trail management and verification
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.services.blockchain_audit import (
    get_blockchain_service, 
    record_audit_event,
    AuditEventType
)

router = APIRouter()

# Pydantic models for API
class AuditEventRequest(BaseModel):
    event_type: str
    entity_type: str
    entity_id: str
    data: Dict[str, Any]
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None

class BlockchainVerificationResponse(BaseModel):
    is_valid: bool
    total_blocks: int
    errors: List[str]
    verification_time: datetime

class AuditTrailResponse(BaseModel):
    total_records: int
    records: List[Dict[str, Any]]
    filters_applied: Dict[str, Any]

class BlockchainStatsResponse(BaseModel):
    total_blocks: int
    total_transactions: int
    pending_transactions: int
    recent_activity: int
    event_type_distribution: List[Dict[str, Any]]
    blockchain_length: int
    last_block_time: Optional[str]

@router.post("/record-event")
def record_blockchain_audit_event(
    request: AuditEventRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Record an audit event to the blockchain
    """
    try:
        # Validate event type
        valid_event_types = [e.value for e in AuditEventType]
        if request.event_type not in valid_event_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid event type. Must be one of: {valid_event_types}"
            )
        
        # Record the audit event
        transaction_hash = record_audit_event(
            event_type=request.event_type,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            user_id=str(current_user.id),
            data=request.data,
            previous_state=request.previous_state,
            new_state=request.new_state
        )
        
        return {
            "status": "success",
            "transaction_hash": transaction_hash,
            "message": "Audit event recorded to blockchain",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record audit event: {str(e)}")

@router.get("/verify", response_model=BlockchainVerificationResponse)
def verify_blockchain_integrity(
    current_user: User = Depends(get_current_active_user)
):
    """
    Verify the integrity of the blockchain
    """
    try:
        blockchain_service = get_blockchain_service()
        verification_start = datetime.now()
        
        results = blockchain_service.verify_blockchain_integrity()
        
        return BlockchainVerificationResponse(
            is_valid=results["is_valid"],
            total_blocks=results["total_blocks"],
            errors=results["errors"],
            verification_time=verification_start
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blockchain verification failed: {str(e)}")

@router.get("/audit-trail", response_model=AuditTrailResponse)
def get_audit_trail(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get audit trail records with optional filters
    """
    try:
        blockchain_service = get_blockchain_service()
        
        records = blockchain_service.get_audit_trail(
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        filters_applied = {}
        if entity_type:
            filters_applied["entity_type"] = entity_type
        if entity_id:
            filters_applied["entity_id"] = entity_id
        if event_type:
            filters_applied["event_type"] = event_type
        if start_date:
            filters_applied["start_date"] = start_date.isoformat()
        if end_date:
            filters_applied["end_date"] = end_date.isoformat()
        filters_applied["limit"] = limit
        
        return AuditTrailResponse(
            total_records=len(records),
            records=records,
            filters_applied=filters_applied
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audit trail: {str(e)}")

@router.get("/stats", response_model=BlockchainStatsResponse)
def get_blockchain_statistics(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get blockchain statistics and metrics
    """
    try:
        blockchain_service = get_blockchain_service()
        stats = blockchain_service.get_blockchain_stats()
        
        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["error"])
        
        return BlockchainStatsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get blockchain stats: {str(e)}")

@router.post("/force-block")
def force_new_block_creation(
    current_user: User = Depends(get_current_active_user)
):
    """
    Force creation of a new block with pending transactions
    (Admin only)
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        blockchain_service = get_blockchain_service()
        blockchain_service.force_block_creation()
        
        return {
            "status": "success",
            "message": "New block created with pending transactions",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create block: {str(e)}")

@router.get("/event-types")
def get_available_event_types(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of available audit event types
    """
    event_types = []
    for event_type in AuditEventType:
        event_types.append({
            "value": event_type.value,
            "description": event_type.value.replace("_", " ").title()
        })
    
    return {
        "event_types": event_types,
        "total_types": len(event_types)
    }

@router.get("/entity/{entity_type}/{entity_id}/history")
def get_entity_audit_history(
    entity_type: str,
    entity_id: str,
    limit: int = Query(50, ge=1, le=500, description="Maximum number of records"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get complete audit history for a specific entity
    """
    try:
        blockchain_service = get_blockchain_service()
        
        records = blockchain_service.get_audit_trail(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit
        )
        
        # Group records by event type for summary
        event_summary = {}
        for record in records:
            event_type = record["event_type"]
            if event_type not in event_summary:
                event_summary[event_type] = 0
            event_summary[event_type] += 1
        
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "total_events": len(records),
            "event_summary": event_summary,
            "records": records
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entity history: {str(e)}")

@router.get("/compliance/report")
def generate_compliance_audit_report(
    start_date: datetime = Query(..., description="Report start date"),
    end_date: datetime = Query(..., description="Report end date"),
    entity_types: Optional[List[str]] = Query(None, description="Filter by entity types"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate a compliance audit report for regulatory purposes
    """
    try:
        blockchain_service = get_blockchain_service()
        
        # Get all records in the date range
        all_records = []
        if entity_types:
            for entity_type in entity_types:
                records = blockchain_service.get_audit_trail(
                    entity_type=entity_type,
                    start_date=start_date,
                    end_date=end_date,
                    limit=10000  # Large limit for comprehensive report
                )
                all_records.extend(records)
        else:
            all_records = blockchain_service.get_audit_trail(
                start_date=start_date,
                end_date=end_date,
                limit=10000
            )
        
        # Generate summary statistics
        event_counts = {}
        entity_counts = {}
        user_activity = {}
        daily_activity = {}
        
        for record in all_records:
            # Event type counts
            event_type = record["event_type"]
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            # Entity type counts
            entity_type = record["entity_type"]
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            
            # User activity
            user_id = record.get("user_id", "system")
            user_activity[user_id] = user_activity.get(user_id, 0) + 1
            
            # Daily activity
            date_str = record["timestamp"][:10]  # Extract date part
            daily_activity[date_str] = daily_activity.get(date_str, 0) + 1
        
        # Verify blockchain integrity for the report
        verification_results = blockchain_service.verify_blockchain_integrity()
        
        report = {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_audit_events": len(all_records),
                "unique_event_types": len(event_counts),
                "unique_entity_types": len(entity_counts),
                "active_users": len(user_activity),
                "blockchain_verified": verification_results["is_valid"]
            },
            "event_type_breakdown": [
                {"event_type": k, "count": v, "percentage": round(v/len(all_records)*100, 2)}
                for k, v in sorted(event_counts.items(), key=lambda x: x[1], reverse=True)
            ],
            "entity_type_breakdown": [
                {"entity_type": k, "count": v, "percentage": round(v/len(all_records)*100, 2)}
                for k, v in sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)
            ],
            "user_activity": [
                {"user_id": k, "actions": v}
                for k, v in sorted(user_activity.items(), key=lambda x: x[1], reverse=True)
            ][:20],  # Top 20 most active users
            "daily_activity": [
                {"date": k, "events": v}
                for k, v in sorted(daily_activity.items())
            ],
            "blockchain_integrity": verification_results,
            "generated_at": datetime.now().isoformat(),
            "generated_by": current_user.email
        }
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate compliance report: {str(e)}")

@router.post("/admin/reindex")
def reindex_blockchain(
    current_user: User = Depends(get_current_active_user)
):
    """
    Reindex the blockchain (Admin only - for maintenance)
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        # This would typically reload the blockchain from database
        # and verify all blocks
        blockchain_service = get_blockchain_service()
        blockchain_service._load_blockchain()
        
        verification_results = blockchain_service.verify_blockchain_integrity()
        
        return {
            "status": "success" if verification_results["is_valid"] else "warning",
            "message": "Blockchain reindexed",
            "verification": verification_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reindex blockchain: {str(e)}")