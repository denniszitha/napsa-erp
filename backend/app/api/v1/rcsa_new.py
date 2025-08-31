from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from uuid import UUID
from datetime import datetime, timedelta

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.rcsa import (
    RCSATemplate, RCSAQuestion, RCSAAssessment, RCSAResponse, 
    RCSAActionItem, RCSASchedule, RCSAStatus, RCSAFrequency
)
from app.schemas.rcsa import (
    RCSATemplateCreate, RCSATemplateUpdate, RCSATemplateResponse,
    RCSAQuestionCreate, RCSAQuestionUpdate, RCSAQuestionResponse,
    RCSAAssessmentCreate, RCSAAssessmentUpdate, RCSAAssessmentResponse,
    RCSAResponseCreate, RCSAResponseUpdate, RCSAResponseResponse,
    RCSAActionItemCreate, RCSAActionItemUpdate, RCSAActionItemResponse,
    RCSAScheduleCreate, RCSAScheduleUpdate, RCSAScheduleResponse,
    RCSADashboardSummary, RCSABulkCreateAssessments
)
from app.schemas.base import PaginatedResponse

router = APIRouter()

# RCSA Templates
@router.get("/templates", response_model=PaginatedResponse)
def get_rcsa_templates(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
):
    """Get RCSA templates with pagination and filtering"""
    query = db.query(RCSATemplate)
    
    if department:
        query = query.filter(RCSATemplate.department == department)
    if is_active is not None:
        query = query.filter(RCSATemplate.is_active == is_active)
    
    total = query.count()
    templates = query.offset(skip).limit(limit).all()
    
    # Add counts
    for template in templates:
        template.questions_count = len(template.questions)
        template.assessments_count = len(template.assessments)
    
    return PaginatedResponse(
        total=total,
        skip=skip, 
        limit=limit,
        data=[RCSATemplateResponse.model_validate(t) for t in templates]
    )

@router.post("/templates", response_model=RCSATemplateResponse)
def create_rcsa_template(
    template_in: RCSATemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new RCSA template"""
    template = RCSATemplate(
        **template_in.model_dump(),
        created_by_id=current_user.id
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return RCSATemplateResponse.model_validate(template)

@router.get("/templates/{template_id}", response_model=RCSATemplateResponse)
def get_rcsa_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get RCSA template by ID"""
    template = db.query(RCSATemplate).filter(RCSATemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template.questions_count = len(template.questions)
    template.assessments_count = len(template.assessments)
    
    return RCSATemplateResponse.model_validate(template)

# RCSA Questions
@router.get("/templates/{template_id}/questions", response_model=List[RCSAQuestionResponse])
def get_template_questions(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get questions for a specific template"""
    template = db.query(RCSATemplate).filter(RCSATemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    questions = db.query(RCSAQuestion).filter(
        RCSAQuestion.template_id == template_id
    ).order_by(RCSAQuestion.order_number).all()
    
    return [RCSAQuestionResponse.model_validate(q) for q in questions]

@router.post("/templates/{template_id}/questions", response_model=RCSAQuestionResponse)
def create_template_question(
    template_id: UUID,
    question_in: RCSAQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Add a question to a template"""
    template = db.query(RCSATemplate).filter(RCSATemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Override template_id from URL
    question_data = question_in.model_dump()
    question_data['template_id'] = template_id
    
    question = RCSAQuestion(**question_data)
    db.add(question)
    db.commit()
    db.refresh(question)
    
    return RCSAQuestionResponse.model_validate(question)

# RCSA Assessments
@router.get("/assessments", response_model=PaginatedResponse)
def get_rcsa_assessments(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department: Optional[str] = None,
    status: Optional[RCSAStatus] = None,
    assessor_id: Optional[UUID] = None,
    template_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_active_user),
):
    """Get RCSA assessments with filtering"""
    query = db.query(RCSAAssessment).options(
        joinedload(RCSAAssessment.template)
    )
    
    if department:
        query = query.filter(RCSAAssessment.department == department)
    if status:
        query = query.filter(RCSAAssessment.status == status)
    if assessor_id:
        query = query.filter(RCSAAssessment.assessor_id == assessor_id)
    if template_id:
        query = query.filter(RCSAAssessment.template_id == template_id)
    
    total = query.count()
    assessments = query.offset(skip).limit(limit).all()
    
    # Enrich with related data
    for assessment in assessments:
        assessment.template_name = assessment.template.name if assessment.template else None
        assessment.questions_count = len(assessment.template.questions) if assessment.template else 0
        assessment.responses_count = len(assessment.responses)
        assessment.action_items_count = len(assessment.action_items)
    
    return PaginatedResponse(
        total=total,
        skip=skip,
        limit=limit,
        data=[RCSAAssessmentResponse.model_validate(a) for a in assessments]
    )

@router.post("/assessments", response_model=RCSAAssessmentResponse)
def create_rcsa_assessment(
    assessment_in: RCSAAssessmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new RCSA assessment"""
    # Verify template exists
    template = db.query(RCSATemplate).filter(
        RCSATemplate.id == assessment_in.template_id
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    assessment = RCSAAssessment(**assessment_in.model_dump())
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    
    # Set template name
    assessment.template_name = template.name
    assessment.questions_count = len(template.questions)
    
    return RCSAAssessmentResponse.model_validate(assessment)

@router.get("/assessments/{assessment_id}", response_model=RCSAAssessmentResponse)
def get_rcsa_assessment(
    assessment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get RCSA assessment by ID"""
    assessment = db.query(RCSAAssessment).options(
        joinedload(RCSAAssessment.template)
    ).filter(RCSAAssessment.id == assessment_id).first()
    
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Enrich with counts and names
    assessment.template_name = assessment.template.name if assessment.template else None
    assessment.questions_count = len(assessment.template.questions) if assessment.template else 0
    assessment.responses_count = len(assessment.responses)
    assessment.action_items_count = len(assessment.action_items)
    
    return RCSAAssessmentResponse.model_validate(assessment)

# RCSA Responses
@router.get("/assessments/{assessment_id}/responses", response_model=List[RCSAResponseResponse])
def get_assessment_responses(
    assessment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get responses for an assessment"""
    assessment = db.query(RCSAAssessment).filter(RCSAAssessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    responses = db.query(RCSAResponse).options(
        joinedload(RCSAResponse.question)
    ).filter(RCSAResponse.assessment_id == assessment_id).all()
    
    # Enrich with question data
    for response in responses:
        if response.question:
            response.question_text = response.question.question_text
            response.question_category = response.question.category
            response.question_weight = response.question.weight
    
    return [RCSAResponseResponse.model_validate(r) for r in responses]

@router.post("/assessments/{assessment_id}/responses", response_model=RCSAResponseResponse)
def create_assessment_response(
    assessment_id: UUID,
    response_in: RCSAResponseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Submit response to assessment question"""
    assessment = db.query(RCSAAssessment).filter(RCSAAssessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Override assessment_id from URL
    response_data = response_in.model_dump()
    response_data['assessment_id'] = assessment_id
    response_data['responded_by_id'] = current_user.id
    
    # Calculate score based on response type
    question = db.query(RCSAQuestion).filter(
        RCSAQuestion.id == response_in.question_id
    ).first()
    
    score = 0.0
    if question:
        if response_in.rating_value:
            score = (response_in.rating_value / 5.0) * question.weight
        elif response_in.boolean_value is not None:
            score = (1.0 if response_in.boolean_value else 0.0) * question.weight
        response_data['score'] = score
    
    response = RCSAResponse(**response_data)
    db.add(response)
    db.commit()
    db.refresh(response)
    
    # Update assessment completion percentage
    update_assessment_completion(db, assessment_id)
    
    return RCSAResponseResponse.model_validate(response)

# Action Items
@router.get("/assessments/{assessment_id}/action-items", response_model=List[RCSAActionItemResponse])
def get_assessment_action_items(
    assessment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get action items for an assessment"""
    action_items = db.query(RCSAActionItem).filter(
        RCSAActionItem.assessment_id == assessment_id
    ).all()
    
    return [RCSAActionItemResponse.model_validate(item) for item in action_items]

@router.post("/assessments/{assessment_id}/action-items", response_model=RCSAActionItemResponse)
def create_action_item(
    assessment_id: UUID,
    item_in: RCSAActionItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create action item for assessment"""
    assessment = db.query(RCSAAssessment).filter(RCSAAssessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    item_data = item_in.model_dump()
    item_data['assessment_id'] = assessment_id
    
    action_item = RCSAActionItem(**item_data)
    db.add(action_item)
    db.commit()
    db.refresh(action_item)
    
    return RCSAActionItemResponse.model_validate(action_item)

# Dashboard and Summary
@router.get("/dashboard/summary", response_model=RCSADashboardSummary)
def get_rcsa_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get RCSA dashboard summary statistics"""
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Template count
    total_templates = db.query(RCSATemplate).filter(RCSATemplate.is_active == True).count()
    
    # Assessment counts
    total_assessments = db.query(RCSAAssessment).count()
    pending_assessments = db.query(RCSAAssessment).filter(
        RCSAAssessment.status.in_([RCSAStatus.draft, RCSAStatus.scheduled, RCSAStatus.in_progress])
    ).count()
    
    overdue_assessments = db.query(RCSAAssessment).filter(
        and_(
            RCSAAssessment.due_date < now,
            RCSAAssessment.status != RCSAStatus.approved
        )
    ).count()
    
    completed_this_month = db.query(RCSAAssessment).filter(
        and_(
            RCSAAssessment.completed_date >= month_start,
            RCSAAssessment.status == RCSAStatus.approved
        )
    ).count()
    
    # Action item counts
    action_items_open = db.query(RCSAActionItem).filter(
        RCSAActionItem.status.in_(["open", "in_progress"])
    ).count()
    
    action_items_overdue = db.query(RCSAActionItem).filter(
        and_(
            RCSAActionItem.due_date < now,
            RCSAActionItem.status != "completed"
        )
    ).count()
    
    # Completion rate
    completion_rate = 0.0
    if total_assessments > 0:
        completed_assessments = db.query(RCSAAssessment).filter(
            RCSAAssessment.status == RCSAStatus.approved
        ).count()
        completion_rate = (completed_assessments / total_assessments) * 100
    
    return RCSADashboardSummary(
        total_templates=total_templates,
        total_assessments=total_assessments,
        pending_assessments=pending_assessments,
        overdue_assessments=overdue_assessments,
        completed_this_month=completed_this_month,
        action_items_open=action_items_open,
        action_items_overdue=action_items_overdue,
        completion_rate=completion_rate
    )

# Bulk Operations
@router.post("/assessments/bulk-create")
def bulk_create_assessments(
    bulk_data: RCSABulkCreateAssessments,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create multiple assessments for different departments"""
    template = db.query(RCSATemplate).filter(RCSATemplate.id == bulk_data.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    created_assessments = []
    for department in bulk_data.departments:
        assessor_id = bulk_data.assessor_assignments.get(department) if bulk_data.assessor_assignments else None
        
        assessment = RCSAAssessment(
            template_id=bulk_data.template_id,
            title=f"{template.name} - {department} - {bulk_data.assessment_period}",
            department=department,
            assessment_period=bulk_data.assessment_period,
            due_date=bulk_data.due_date,
            assessor_id=assessor_id,
            status=RCSAStatus.scheduled
        )
        db.add(assessment)
        created_assessments.append(assessment)
    
    db.commit()
    
    return {
        "success": True,
        "created_count": len(created_assessments),
        "assessments": [{"id": str(a.id), "department": a.department} for a in created_assessments]
    }

# Helper functions
def update_assessment_completion(db: Session, assessment_id: UUID):
    """Update assessment completion percentage based on responses"""
    assessment = db.query(RCSAAssessment).options(
        joinedload(RCSAAssessment.template).joinedload(RCSATemplate.questions)
    ).filter(RCSAAssessment.id == assessment_id).first()
    
    if not assessment or not assessment.template:
        return
    
    total_questions = len(assessment.template.questions)
    if total_questions == 0:
        return
    
    responses_count = db.query(RCSAResponse).filter(
        RCSAResponse.assessment_id == assessment_id
    ).count()
    
    completion_percentage = (responses_count / total_questions) * 100
    assessment.completion_percentage = completion_percentage
    
    # Calculate total score
    total_score = db.query(func.sum(RCSAResponse.score)).filter(
        RCSAResponse.assessment_id == assessment_id
    ).scalar() or 0.0
    
    max_possible_score = sum(q.weight for q in assessment.template.questions)
    
    assessment.total_score = total_score
    assessment.max_possible_score = max_possible_score
    
    # Update status based on completion
    if completion_percentage == 100 and assessment.status == RCSAStatus.in_progress:
        assessment.status = RCSAStatus.submitted
        assessment.completed_date = datetime.utcnow()
    
    db.commit()