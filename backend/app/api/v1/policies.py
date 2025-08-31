from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from uuid import UUID
from datetime import datetime, timezone

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.policy import Policy, PolicyStatus, PolicyCategory, PolicyReview, PolicyApproval
from app.schemas.base import PaginatedResponse
from pydantic import BaseModel

router = APIRouter()

# Schemas
class PolicyCreate(BaseModel):
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    category: str
    risk_category: Optional[str] = None
    department: Optional[str] = None
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    review_date: Optional[datetime] = None
    owner: Optional[str] = None
    compliance_frameworks: Optional[List[str]] = []
    controls: Optional[List[str]] = []
    tags: Optional[List[str]] = []

class PolicyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    effective_date: Optional[datetime] = None
    review_date: Optional[datetime] = None
    compliance_frameworks: Optional[List[str]] = None
    controls: Optional[List[str]] = None

class PolicyApprovalRequest(BaseModel):
    action: str  # approve or reject
    comments: Optional[str] = None

@router.get("/", response_model=PaginatedResponse)
def get_policies(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    """Get all policies with filtering"""
    query = db.query(Policy)
    
    # Apply filters
    if status:
        try:
            status_enum = PolicyStatus(status)
            query = query.filter(Policy.status == status_enum)
        except ValueError:
            pass
    
    if category:
        try:
            category_enum = PolicyCategory(category)
            query = query.filter(Policy.category == category_enum)
        except ValueError:
            pass
    
    if search:
        query = query.filter(
            or_(
                Policy.title.ilike(f"%{search}%"),
                Policy.description.ilike(f"%{search}%"),
                Policy.policy_number.ilike(f"%{search}%")
            )
        )
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    policies = query.offset(skip).limit(limit).all()
    
    # Format response
    data = []
    for policy in policies:
        data.append({
            "id": str(policy.id),
            "policy_number": policy.policy_number,
            "title": policy.title,
            "description": policy.description,
            "category": policy.category.value if policy.category else None,
            "status": policy.status.value if policy.status else None,
            "version": policy.version,
            "effective_date": policy.effective_date.isoformat() if policy.effective_date else None,
            "review_date": policy.review_date.isoformat() if policy.review_date else None,
            "owner": policy.created_by,
            "department": policy.department,
            "created_at": policy.created_at.isoformat() if policy.created_at else None,
            "updated_at": policy.updated_at.isoformat() if policy.updated_at else None
        })
    
    return PaginatedResponse(
        total=total,
        skip=skip,
        limit=limit,
        data=data
    )

@router.post("/", status_code=201)
def create_policy(
    policy_data: PolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new policy"""
    # Generate policy number
    policy_count = db.query(Policy).count()
    policy_number = f"POL-{datetime.now().strftime('%Y')}-{str(policy_count + 1).zfill(4)}"
    
    # Create policy
    policy = Policy(
        policy_number=policy_number,
        title=policy_data.title,
        description=policy_data.description,
        content=policy_data.content,
        category=PolicyCategory(policy_data.category),
        risk_category=policy_data.risk_category,
        department=policy_data.department,
        status=PolicyStatus.draft,
        effective_date=policy_data.effective_date,
        expiry_date=policy_data.expiry_date,
        review_date=policy_data.review_date,
        created_by=current_user.full_name,
        modified_by=current_user.full_name,
        owner_id=current_user.id,
        compliance_frameworks=policy_data.compliance_frameworks,
        controls=policy_data.controls,
        tags=policy_data.tags
    )
    
    db.add(policy)
    db.commit()
    db.refresh(policy)
    
    return {
        "id": str(policy.id),
        "policy_number": policy.policy_number,
        "title": policy.title,
        "status": policy.status.value,
        "message": f"Policy {policy.policy_number} created successfully"
    }

@router.get("/{policy_id}")
def get_policy(
    policy_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific policy"""
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Get reviews and approvals
    reviews = db.query(PolicyReview).filter(PolicyReview.policy_id == policy_id).all()
    approvals = db.query(PolicyApproval).filter(PolicyApproval.policy_id == policy_id).all()
    
    return {
        "id": str(policy.id),
        "policy_number": policy.policy_number,
        "title": policy.title,
        "description": policy.description,
        "content": policy.content,
        "category": policy.category.value if policy.category else None,
        "risk_category": policy.risk_category,
        "department": policy.department,
        "status": policy.status.value if policy.status else None,
        "version": policy.version,
        "effective_date": policy.effective_date.isoformat() if policy.effective_date else None,
        "expiry_date": policy.expiry_date.isoformat() if policy.expiry_date else None,
        "review_date": policy.review_date.isoformat() if policy.review_date else None,
        "created_by": policy.created_by,
        "modified_by": policy.modified_by,
        "approved_by": policy.approved_by,
        "compliance_frameworks": policy.compliance_frameworks or [],
        "controls": policy.controls or [],
        "tags": policy.tags or [],
        "attachments": policy.attachments or [],
        "created_at": policy.created_at.isoformat() if policy.created_at else None,
        "updated_at": policy.updated_at.isoformat() if policy.updated_at else None,
        "reviews": [
            {
                "id": str(r.id),
                "reviewer": str(r.reviewer_id),
                "date": r.review_date.isoformat(),
                "status": r.status,
                "comments": r.comments
            } for r in reviews
        ],
        "approvals": [
            {
                "id": str(a.id),
                "approver": str(a.approver_id),
                "date": a.approval_date.isoformat(),
                "action": a.action,
                "comments": a.comments
            } for a in approvals
        ]
    }

@router.put("/{policy_id}")
def update_policy(
    policy_id: UUID,
    policy_update: PolicyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a policy"""
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Update fields
    if policy_update.title:
        policy.title = policy_update.title
    if policy_update.description:
        policy.description = policy_update.description
    if policy_update.content:
        policy.content = policy_update.content
    if policy_update.category:
        policy.category = PolicyCategory(policy_update.category)
    if policy_update.status:
        old_status = policy.status
        policy.status = PolicyStatus(policy_update.status)
        
        # Update timestamps based on status change
        if policy.status == PolicyStatus.published and old_status != PolicyStatus.published:
            policy.published_at = datetime.now(timezone.utc)
            # Increment version
            version_parts = policy.version.split('.')
            minor_version = int(version_parts[1]) if len(version_parts) > 1 else 0
            policy.version = f"{version_parts[0]}.{minor_version + 1}"
        elif policy.status == PolicyStatus.archived:
            policy.archived_at = datetime.now(timezone.utc)
    
    if policy_update.effective_date:
        policy.effective_date = policy_update.effective_date
    if policy_update.review_date:
        policy.review_date = policy_update.review_date
    if policy_update.compliance_frameworks is not None:
        policy.compliance_frameworks = policy_update.compliance_frameworks
    if policy_update.controls is not None:
        policy.controls = policy_update.controls
    
    policy.modified_by = current_user.full_name
    policy.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    
    return {
        "id": str(policy.id),
        "policy_number": policy.policy_number,
        "title": policy.title,
        "status": policy.status.value,
        "version": policy.version,
        "message": f"Policy {policy.policy_number} updated successfully"
    }

@router.delete("/{policy_id}")
def delete_policy(
    policy_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a policy (soft delete by archiving)"""
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Soft delete by archiving
    policy.status = PolicyStatus.archived
    policy.archived_at = datetime.now(timezone.utc)
    policy.is_current = False
    
    db.commit()
    
    return {"message": f"Policy {policy.policy_number} archived successfully"}

@router.post("/{policy_id}/approve")
def approve_policy(
    policy_id: UUID,
    approval_request: PolicyApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Approve or reject a policy"""
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Create approval record
    approval = PolicyApproval(
        policy_id=policy_id,
        approver_id=current_user.id,
        action=approval_request.action,
        comments=approval_request.comments,
        approval_date=datetime.now(timezone.utc)
    )
    
    db.add(approval)
    
    # Update policy status
    if approval_request.action == "approve":
        policy.status = PolicyStatus.approved
        policy.approved_by = current_user.full_name
    elif approval_request.action == "reject":
        policy.status = PolicyStatus.draft  # Send back to draft
    
    db.commit()
    
    return {
        "policy_id": str(policy.id),
        "action": approval_request.action,
        "status": policy.status.value,
        "message": f"Policy {policy.policy_number} {approval_request.action}d successfully"
    }

@router.post("/{policy_id}/publish")
def publish_policy(
    policy_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Publish an approved policy"""
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    if policy.status != PolicyStatus.approved:
        raise HTTPException(status_code=400, detail="Only approved policies can be published")
    
    policy.status = PolicyStatus.published
    policy.published_at = datetime.now(timezone.utc)
    
    db.commit()
    
    return {
        "policy_id": str(policy.id),
        "status": policy.status.value,
        "published_at": policy.published_at.isoformat(),
        "message": f"Policy {policy.policy_number} published successfully"
    }

@router.get("/stats/summary")
def get_policy_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get policy statistics"""
    total = db.query(Policy).count()
    
    # Count by status
    status_counts = {}
    for status in PolicyStatus:
        count = db.query(Policy).filter(Policy.status == status).count()
        status_counts[status.value] = count
    
    # Count by category
    category_counts = {}
    for category in PolicyCategory:
        count = db.query(Policy).filter(Policy.category == category).count()
        category_counts[category.value] = count
    
    # Policies needing review
    from datetime import timedelta
    review_threshold = datetime.now(timezone.utc) + timedelta(days=30)
    needs_review = db.query(Policy).filter(
        and_(
            Policy.review_date <= review_threshold,
            Policy.status == PolicyStatus.published
        )
    ).count()
    
    return {
        "total_policies": total,
        "by_status": status_counts,
        "by_category": category_counts,
        "needs_review": needs_review,
        "compliance_rate": 85,  # Mock value
        "last_updated": datetime.now(timezone.utc).isoformat()
    }