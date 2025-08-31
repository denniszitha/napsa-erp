"""
RCSA (Risk Control Self-Assessment) API endpoints
Complete implementation for NAPSA requirements
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.rcsa import (
    RCSATemplate, RCSAQuestion, RCSAAssessment, 
    RCSAResponse, RCSAActionItem, RCSASchedule,
    RCSANotification, AssessmentStatus, ResponseType
)
from app.schemas.rcsa import (
    RCSATemplateCreate, RCSATemplateUpdate, RCSATemplateResponse,
    RCSAQuestionCreate, RCSAQuestionUpdate, RCSAQuestionResponse,
    RCSAAssessmentCreate, RCSAAssessmentUpdate, RCSAAssessmentResponse,
    RCSAResponseCreate, RCSAResponseUpdate, RCSAResponseResponse,
    RCSAActionItemCreate, RCSAActionItemUpdate, RCSAActionItemResponse,
    RCSAScheduleCreate, RCSAScheduleUpdate, RCSAScheduleResponse,
    RCSADashboard, RCSAComplianceReport
)

router = APIRouter(prefix="/rcsa", tags=["RCSA"])

# Template Management Endpoints
@router.post("/templates", response_model=RCSATemplateResponse)
def create_template(
    template: RCSATemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new RCSA template"""
    db_template = RCSATemplate(
        **template.dict(),
        created_by=current_user.id,
        created_at=datetime.utcnow()
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.get("/templates", response_model=List[RCSATemplateResponse])
def get_templates(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all RCSA templates"""
    query = db.query(RCSATemplate)
    if active_only:
        query = query.filter(RCSATemplate.is_active == True)
    templates = query.offset(skip).limit(limit).all()
    return templates

@router.get("/templates/{template_id}", response_model=RCSATemplateResponse)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific RCSA template"""
    template = db.query(RCSATemplate).filter(RCSATemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@router.put("/templates/{template_id}", response_model=RCSATemplateResponse)
def update_template(
    template_id: int,
    template_update: RCSATemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an RCSA template"""
    template = db.query(RCSATemplate).filter(RCSATemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    for field, value in template_update.dict(exclude_unset=True).items():
        setattr(template, field, value)
    
    template.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(template)
    return template

@router.delete("/templates/{template_id}")
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an RCSA template (soft delete)"""
    template = db.query(RCSATemplate).filter(RCSATemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template.is_active = False
    template.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Template deactivated successfully"}

# Question Management Endpoints
@router.post("/templates/{template_id}/questions", response_model=RCSAQuestionResponse)
def create_question(
    template_id: int,
    question: RCSAQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a question to an RCSA template"""
    template = db.query(RCSATemplate).filter(RCSATemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db_question = RCSAQuestion(
        template_id=template_id,
        **question.dict(),
        created_at=datetime.utcnow()
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

@router.get("/templates/{template_id}/questions", response_model=List[RCSAQuestionResponse])
def get_template_questions(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all questions for a template"""
    questions = db.query(RCSAQuestion).filter(
        RCSAQuestion.template_id == template_id,
        RCSAQuestion.is_active == True
    ).order_by(RCSAQuestion.order).all()
    return questions

# Assessment Management Endpoints
@router.post("/assessments", response_model=RCSAAssessmentResponse)
def create_assessment(
    assessment: RCSAAssessmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new RCSA assessment"""
    db_assessment = RCSAAssessment(
        **assessment.dict(),
        created_by=current_user.id,
        status=AssessmentStatus.PENDING,
        created_at=datetime.utcnow()
    )
    db.add(db_assessment)
    db.commit()
    db.refresh(db_assessment)
    
    # Create notification for the assessor
    notification = RCSANotification(
        assessment_id=db_assessment.id,
        user_id=assessment.assessor_id,
        notification_type='assessment_assigned',
        message=f'You have been assigned a new RCSA assessment: {db_assessment.title}',
        created_at=datetime.utcnow()
    )
    db.add(notification)
    db.commit()
    
    return db_assessment

@router.get("/assessments", response_model=Dict[str, Any])
def get_assessments(
    skip: int = 0,
    limit: int = 100,
    status: Optional[AssessmentStatus] = None,
    department_id: Optional[int] = None,
    assessor_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all RCSA assessments with filters"""
    query = db.query(RCSAAssessment)
    
    if status:
        query = query.filter(RCSAAssessment.status == status)
    if department_id:
        query = query.filter(RCSAAssessment.department_id == department_id)
    if assessor_id:
        query = query.filter(RCSAAssessment.assessor_id == assessor_id)
    
    total = query.count()
    assessments = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": assessments
    }

@router.get("/assessments/{assessment_id}", response_model=RCSAAssessmentResponse)
def get_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific RCSA assessment"""
    assessment = db.query(RCSAAssessment).filter(
        RCSAAssessment.id == assessment_id
    ).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment

@router.put("/assessments/{assessment_id}", response_model=RCSAAssessmentResponse)
def update_assessment(
    assessment_id: int,
    assessment_update: RCSAAssessmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an RCSA assessment"""
    assessment = db.query(RCSAAssessment).filter(
        RCSAAssessment.id == assessment_id
    ).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    for field, value in assessment_update.dict(exclude_unset=True).items():
        setattr(assessment, field, value)
    
    assessment.updated_at = datetime.utcnow()
    
    # Update completion percentage if status changes to completed
    if assessment.status == AssessmentStatus.COMPLETED:
        assessment.completion_percentage = 100
        assessment.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(assessment)
    return assessment

@router.post("/assessments/{assessment_id}/submit")
def submit_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit an assessment for approval"""
    assessment = db.query(RCSAAssessment).filter(
        RCSAAssessment.id == assessment_id
    ).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Check if all required questions are answered
    total_questions = db.query(RCSAQuestion).filter(
        RCSAQuestion.template_id == assessment.template_id,
        RCSAQuestion.is_required == True
    ).count()
    
    answered_questions = db.query(RCSAResponse).filter(
        RCSAResponse.assessment_id == assessment_id
    ).count()
    
    if answered_questions < total_questions:
        raise HTTPException(
            status_code=400, 
            detail=f"Please answer all required questions. {answered_questions}/{total_questions} completed."
        )
    
    assessment.status = AssessmentStatus.SUBMITTED
    assessment.submitted_at = datetime.utcnow()
    assessment.completion_percentage = 100
    db.commit()
    
    return {"message": "Assessment submitted successfully"}

# Response Management Endpoints
@router.post("/assessments/{assessment_id}/responses", response_model=RCSAResponseResponse)
def create_response(
    assessment_id: int,
    response: RCSAResponseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a response to an assessment question"""
    assessment = db.query(RCSAAssessment).filter(
        RCSAAssessment.id == assessment_id
    ).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Check if response already exists
    existing = db.query(RCSAResponse).filter(
        RCSAResponse.assessment_id == assessment_id,
        RCSAResponse.question_id == response.question_id
    ).first()
    
    if existing:
        # Update existing response
        for field, value in response.dict(exclude_unset=True).items():
            setattr(existing, field, value)
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new response
        db_response = RCSAResponse(
            assessment_id=assessment_id,
            **response.dict(),
            responded_by=current_user.id,
            created_at=datetime.utcnow()
        )
        db.add(db_response)
        
        # Update assessment progress
        assessment.status = AssessmentStatus.IN_PROGRESS
        if not assessment.started_at:
            assessment.started_at = datetime.utcnow()
        
        # Calculate completion percentage
        total_questions = db.query(RCSAQuestion).filter(
            RCSAQuestion.template_id == assessment.template_id
        ).count()
        answered_questions = db.query(RCSAResponse).filter(
            RCSAResponse.assessment_id == assessment_id
        ).count() + 1  # Including this new response
        
        assessment.completion_percentage = (answered_questions / total_questions) * 100
        
        db.commit()
        db.refresh(db_response)
        return db_response

@router.get("/assessments/{assessment_id}/responses", response_model=List[RCSAResponseResponse])
def get_assessment_responses(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all responses for an assessment"""
    responses = db.query(RCSAResponse).filter(
        RCSAResponse.assessment_id == assessment_id
    ).all()
    return responses

# Action Items Endpoints
@router.post("/assessments/{assessment_id}/actions", response_model=RCSAActionItemResponse)
def create_action_item(
    assessment_id: int,
    action: RCSAActionItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create an action item from assessment findings"""
    db_action = RCSAActionItem(
        assessment_id=assessment_id,
        **action.dict(),
        created_by=current_user.id,
        created_at=datetime.utcnow()
    )
    db.add(db_action)
    db.commit()
    db.refresh(db_action)
    return db_action

@router.get("/action-items", response_model=List[RCSAActionItemResponse])
def get_action_items(
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    overdue_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get action items with filters"""
    query = db.query(RCSAActionItem)
    
    if status:
        query = query.filter(RCSAActionItem.status == status)
    if assigned_to:
        query = query.filter(RCSAActionItem.assigned_to == assigned_to)
    if overdue_only:
        query = query.filter(
            RCSAActionItem.due_date < datetime.utcnow(),
            RCSAActionItem.status != 'completed'
        )
    
    action_items = query.all()
    return action_items

# Schedule Management Endpoints
@router.post("/schedule", response_model=RCSAScheduleResponse)
def create_schedule(
    schedule: RCSAScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create an RCSA assessment schedule"""
    db_schedule = RCSASchedule(
        **schedule.dict(),
        created_by=current_user.id,
        created_at=datetime.utcnow()
    )
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

@router.get("/schedule", response_model=List[RCSAScheduleResponse])
def get_schedules(
    active_only: bool = True,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get RCSA assessment schedules"""
    query = db.query(RCSASchedule)
    
    if active_only:
        query = query.filter(RCSASchedule.is_active == True)
    if department_id:
        query = query.filter(RCSASchedule.department_id == department_id)
    
    schedules = query.all()
    return schedules

@router.post("/schedule/trigger")
def trigger_scheduled_assessments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually trigger scheduled assessments (usually run by cron job)"""
    today = datetime.utcnow().date()
    
    # Find schedules due for assessment
    schedules = db.query(RCSASchedule).filter(
        RCSASchedule.is_active == True,
        or_(
            RCSASchedule.last_assessment_date == None,
            RCSASchedule.next_assessment_date <= today
        )
    ).all()
    
    created_assessments = []
    
    for schedule in schedules:
        # Create assessment
        assessment = RCSAAssessment(
            template_id=schedule.template_id,
            department_id=schedule.department_id,
            assessor_id=schedule.default_assessor_id,
            title=f"{schedule.assessment_name} - {today}",
            description=f"Scheduled assessment for {schedule.frequency} review",
            due_date=today + timedelta(days=schedule.days_to_complete or 14),
            created_by=current_user.id,
            status=AssessmentStatus.PENDING,
            created_at=datetime.utcnow()
        )
        db.add(assessment)
        
        # Update schedule
        schedule.last_assessment_date = today
        
        # Calculate next assessment date based on frequency
        if schedule.frequency == 'monthly':
            schedule.next_assessment_date = today + timedelta(days=30)
        elif schedule.frequency == 'quarterly':
            schedule.next_assessment_date = today + timedelta(days=90)
        elif schedule.frequency == 'semi-annual':
            schedule.next_assessment_date = today + timedelta(days=180)
        elif schedule.frequency == 'annual':
            schedule.next_assessment_date = today + timedelta(days=365)
        
        created_assessments.append(assessment)
    
    db.commit()
    
    return {
        "message": f"Created {len(created_assessments)} scheduled assessments",
        "assessments": [{"id": a.id, "title": a.title} for a in created_assessments]
    }

# Dashboard and Reporting Endpoints
@router.get("/dashboard", response_model=RCSADashboard)
def get_rcsa_dashboard(
    department_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get RCSA dashboard statistics"""
    query = db.query(RCSAAssessment)
    
    if department_id:
        query = query.filter(RCSAAssessment.department_id == department_id)
    if date_from:
        query = query.filter(RCSAAssessment.created_at >= date_from)
    if date_to:
        query = query.filter(RCSAAssessment.created_at <= date_to)
    
    # Calculate statistics
    total_assessments = query.count()
    completed = query.filter(RCSAAssessment.status == AssessmentStatus.COMPLETED).count()
    in_progress = query.filter(RCSAAssessment.status == AssessmentStatus.IN_PROGRESS).count()
    pending = query.filter(RCSAAssessment.status == AssessmentStatus.PENDING).count()
    overdue = query.filter(
        RCSAAssessment.due_date < datetime.utcnow(),
        RCSAAssessment.status != AssessmentStatus.COMPLETED
    ).count()
    
    # Average completion time
    completed_assessments = query.filter(
        RCSAAssessment.status == AssessmentStatus.COMPLETED,
        RCSAAssessment.completed_at != None,
        RCSAAssessment.started_at != None
    ).all()
    
    avg_completion_days = 0
    if completed_assessments:
        total_days = sum(
            (a.completed_at - a.started_at).days 
            for a in completed_assessments
        )
        avg_completion_days = total_days / len(completed_assessments)
    
    # Action items statistics
    action_query = db.query(RCSAActionItem)
    if department_id:
        action_query = action_query.join(RCSAAssessment).filter(
            RCSAAssessment.department_id == department_id
        )
    
    total_actions = action_query.count()
    open_actions = action_query.filter(RCSAActionItem.status != 'completed').count()
    overdue_actions = action_query.filter(
        RCSAActionItem.due_date < datetime.utcnow(),
        RCSAActionItem.status != 'completed'
    ).count()
    
    return {
        "total_assessments": total_assessments,
        "completed_assessments": completed,
        "in_progress_assessments": in_progress,
        "pending_assessments": pending,
        "overdue_assessments": overdue,
        "completion_rate": (completed / total_assessments * 100) if total_assessments > 0 else 0,
        "average_completion_days": avg_completion_days,
        "total_action_items": total_actions,
        "open_action_items": open_actions,
        "overdue_action_items": overdue_actions,
        "upcoming_assessments": db.query(RCSASchedule).filter(
            RCSASchedule.next_assessment_date <= datetime.utcnow().date() + timedelta(days=30)
        ).count()
    }

@router.get("/compliance-report", response_model=RCSAComplianceReport)
def get_compliance_report(
    year: int = Query(default=datetime.utcnow().year),
    quarter: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate RCSA compliance report"""
    # Define date range
    if quarter:
        start_month = (quarter - 1) * 3 + 1
        end_month = start_month + 2
        date_from = datetime(year, start_month, 1)
        if end_month == 12:
            date_to = datetime(year + 1, 1, 1)
        else:
            date_to = datetime(year, end_month + 1, 1)
    else:
        date_from = datetime(year, 1, 1)
        date_to = datetime(year + 1, 1, 1)
    
    # Get assessments in period
    assessments = db.query(RCSAAssessment).filter(
        RCSAAssessment.created_at >= date_from,
        RCSAAssessment.created_at < date_to
    ).all()
    
    # Calculate compliance metrics
    total = len(assessments)
    completed_on_time = len([
        a for a in assessments 
        if a.status == AssessmentStatus.COMPLETED and 
        (a.completed_at <= a.due_date if a.completed_at and a.due_date else False)
    ])
    
    # Get department compliance
    dept_compliance = db.query(
        RCSAAssessment.department_id,
        func.count(RCSAAssessment.id).label('total'),
        func.sum(
            func.cast(
                RCSAAssessment.status == AssessmentStatus.COMPLETED, 
                Integer
            )
        ).label('completed')
    ).filter(
        RCSAAssessment.created_at >= date_from,
        RCSAAssessment.created_at < date_to
    ).group_by(RCSAAssessment.department_id).all()
    
    department_compliance = [
        {
            "department_id": d.department_id,
            "total_assessments": d.total,
            "completed_assessments": d.completed or 0,
            "compliance_rate": ((d.completed or 0) / d.total * 100) if d.total > 0 else 0
        }
        for d in dept_compliance
    ]
    
    return {
        "period": f"{year}" + (f" Q{quarter}" if quarter else ""),
        "total_assessments": total,
        "completed_assessments": len([
            a for a in assessments 
            if a.status == AssessmentStatus.COMPLETED
        ]),
        "on_time_completion": completed_on_time,
        "compliance_rate": (completed_on_time / total * 100) if total > 0 else 0,
        "department_compliance": department_compliance,
        "high_risk_findings": db.query(RCSAResponse).filter(
            RCSAResponse.risk_rating == 'high',
            RCSAResponse.created_at >= date_from,
            RCSAResponse.created_at < date_to
        ).count(),
        "action_items_created": db.query(RCSAActionItem).filter(
            RCSAActionItem.created_at >= date_from,
            RCSAActionItem.created_at < date_to
        ).count(),
        "action_items_closed": db.query(RCSAActionItem).filter(
            RCSAActionItem.created_at >= date_from,
            RCSAActionItem.created_at < date_to,
            RCSAActionItem.status == 'completed'
        ).count()
    }

@router.post("/bulk-create-assessments")
def bulk_create_assessments(
    template_id: int,
    department_ids: List[int],
    due_date: datetime,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create multiple assessments for different departments"""
    template = db.query(RCSATemplate).filter(RCSATemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    created_assessments = []
    
    for dept_id in department_ids:
        assessment = RCSAAssessment(
            template_id=template_id,
            department_id=dept_id,
            title=f"{template.name} - Department {dept_id}",
            description=template.description,
            due_date=due_date,
            created_by=current_user.id,
            status=AssessmentStatus.PENDING,
            created_at=datetime.utcnow()
        )
        db.add(assessment)
        created_assessments.append(assessment)
    
    db.commit()
    
    return {
        "message": f"Created {len(created_assessments)} assessments",
        "assessment_ids": [a.id for a in created_assessments]
    }