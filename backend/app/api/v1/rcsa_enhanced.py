"""
Enhanced RCSA CRUD API
Complete Risk Control Self-Assessment operations with workflow support
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from pydantic import BaseModel, Field, validator
from enum import Enum

from app.api.deps import get_db, get_current_active_user
from app.models.user import User

router = APIRouter()

# Enums
class AssessmentStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ResponseType(str, Enum):
    YES_NO = "yes_no"
    SCALE = "scale"
    TEXT = "text"
    MULTIPLE_CHOICE = "multiple_choice"
    NUMERIC = "numeric"

class ActionPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Pydantic Models
class RCSATemplateBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    category: str = Field(..., max_length=100)
    version: str = Field(default="1.0", max_length=20)
    is_active: bool = True
    applicable_departments: Optional[List[str]] = []
    risk_categories: Optional[List[str]] = []
    frequency: str = Field(default="quarterly", pattern="^(monthly|quarterly|semi-annually|annually)$")

class RCSATemplateCreate(RCSATemplateBase):
    pass

class RCSAQuestionBase(BaseModel):
    question_text: str = Field(..., min_length=10)
    question_type: ResponseType
    category: str = Field(..., max_length=100)
    weight: float = Field(default=1.0, ge=0, le=10)
    is_mandatory: bool = True
    help_text: Optional[str] = None
    options: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    
    @validator('options')
    def validate_options(cls, v, values):
        if values.get('question_type') == ResponseType.MULTIPLE_CHOICE and not v:
            raise ValueError('Options required for multiple choice questions')
        return v

class RCSAAssessmentBase(BaseModel):
    template_id: int
    department_id: int
    assessment_period: str = Field(..., pattern="^\\d{4}-Q[1-4]$|^\\d{4}-\\d{2}$")
    scheduled_date: date
    due_date: date
    assigned_to: int

class RCSAAssessmentCreate(RCSAAssessmentBase):
    pass

class RCSAResponseBase(BaseModel):
    assessment_id: int
    question_id: int
    response_value: str
    response_score: Optional[float] = None
    comments: Optional[str] = None
    evidence_url: Optional[str] = None

class RCSAActionItemBase(BaseModel):
    assessment_id: int
    identified_issue: str
    recommended_action: str
    priority: ActionPriority
    assigned_to: int
    due_date: date
    estimated_cost: Optional[float] = None
    business_impact: Optional[str] = None

# Response Models
class RCSATemplateResponse(RCSATemplateBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    question_count: Optional[int] = 0
    
    class Config:
        orm_mode = True

class RCSAAssessmentResponse(RCSAAssessmentBase):
    id: int
    status: AssessmentStatus
    completion_percentage: float
    risk_score: Optional[float]
    submitted_at: Optional[datetime]
    approved_at: Optional[datetime]
    approved_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# CRUD Endpoints

@router.get("/templates", response_model=List[Dict[str, Any]])
def get_rcsa_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    is_active: bool = Query(True),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all RCSA templates with filtering"""
    
    query = """
        SELECT 
            t.*,
            u.full_name as created_by_name,
            COUNT(DISTINCT q.id) as question_count,
            COUNT(DISTINCT a.id) as assessment_count
        FROM rcsa_templates t
        LEFT JOIN users u ON t.created_by = u.id
        LEFT JOIN rcsa_questions q ON q.template_id = t.id
        LEFT JOIN rcsa_assessments a ON a.template_id = t.id
        WHERE 1=1
    """
    
    params = {"skip": skip, "limit": limit}
    
    if category:
        query += " AND t.category = :category"
        params["category"] = category
    
    if is_active is not None:
        query += " AND t.is_active = :is_active"
        params["is_active"] = is_active
    
    if search:
        query += " AND (t.name ILIKE :search OR t.description ILIKE :search)"
        params["search"] = f"%{search}%"
    
    query += """
        GROUP BY t.id, u.full_name
        ORDER BY t.created_at DESC
        LIMIT :limit OFFSET :skip
    """
    
    result = db.execute(query, params)
    return [dict(row) for row in result]

@router.get("/templates/{template_id}", response_model=Dict[str, Any])
def get_rcsa_template(
    template_id: int,
    include_questions: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed RCSA template information"""
    
    query = """
        SELECT 
            t.*,
            u.full_name as created_by_name,
            COUNT(DISTINCT a.id) as total_assessments,
            COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'completed') as completed_assessments
        FROM rcsa_templates t
        LEFT JOIN users u ON t.created_by = u.id
        LEFT JOIN rcsa_assessments a ON a.template_id = t.id
        WHERE t.id = :template_id
        GROUP BY t.id, u.full_name
    """
    
    result = db.execute(query, {"template_id": template_id}).first()
    if not result:
        raise HTTPException(status_code=404, detail="RCSA template not found")
    
    template = dict(result)
    
    if include_questions:
        questions_query = """
            SELECT * FROM rcsa_questions
            WHERE template_id = :template_id
            ORDER BY category, id
        """
        questions = db.execute(questions_query, {"template_id": template_id})
        template['questions'] = [dict(q) for q in questions]
    
    return template

@router.post("/templates", response_model=RCSATemplateResponse, status_code=status.HTTP_201_CREATED)
def create_rcsa_template(
    template: RCSATemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new RCSA template"""
    
    query = """
        INSERT INTO rcsa_templates 
        (name, description, category, version, is_active, applicable_departments,
         risk_categories, frequency, created_by, created_at, updated_at)
        VALUES (:name, :description, :category, :version, :is_active, :applicable_departments,
                :risk_categories, :frequency, :created_by, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        RETURNING *
    """
    
    params = template.dict()
    params['created_by'] = current_user.id
    params['applicable_departments'] = params.get('applicable_departments', [])
    params['risk_categories'] = params.get('risk_categories', [])
    
    result = db.execute(query, params).first()
    db.commit()
    
    return dict(result)

@router.post("/templates/{template_id}/questions", status_code=status.HTTP_201_CREATED)
def add_template_questions(
    template_id: int,
    questions: List[RCSAQuestionBase],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add questions to an RCSA template"""
    
    # Verify template exists
    template = db.execute(
        "SELECT id FROM rcsa_templates WHERE id = :id",
        {"id": template_id}
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="RCSA template not found")
    
    inserted_ids = []
    for question in questions:
        query = """
            INSERT INTO rcsa_questions 
            (template_id, question_text, question_type, category, weight, is_mandatory,
             help_text, options, min_value, max_value, created_at)
            VALUES (:template_id, :question_text, :question_type, :category, :weight, :is_mandatory,
                    :help_text, :options, :min_value, :max_value, CURRENT_TIMESTAMP)
            RETURNING id
        """
        
        params = question.dict()
        params['template_id'] = template_id
        
        result = db.execute(query, params).first()
        inserted_ids.append(result['id'])
    
    db.commit()
    
    return {
        "message": f"Added {len(questions)} questions to template",
        "question_ids": inserted_ids
    }

@router.get("/assessments", response_model=List[Dict[str, Any]])
def get_rcsa_assessments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[AssessmentStatus] = Query(None),
    department_id: Optional[int] = Query(None),
    assigned_to: Optional[int] = Query(None),
    period: Optional[str] = Query(None),
    overdue_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all RCSA assessments with filtering"""
    
    query = """
        SELECT 
            a.*,
            t.name as template_name,
            ou.unit_name as department_name,
            u.full_name as assigned_to_name,
            approver.full_name as approved_by_name,
            COUNT(DISTINCT r.id) as response_count,
            COUNT(DISTINCT q.id) as question_count,
            CASE 
                WHEN COUNT(q.id) > 0 
                THEN (COUNT(DISTINCT r.id)::float / COUNT(DISTINCT q.id) * 100)
                ELSE 0 
            END as completion_percentage
        FROM rcsa_assessments a
        JOIN rcsa_templates t ON a.template_id = t.id
        LEFT JOIN organizational_units ou ON a.department_id = ou.id
        LEFT JOIN users u ON a.assigned_to = u.id
        LEFT JOIN users approver ON a.approved_by = approver.id
        LEFT JOIN rcsa_questions q ON q.template_id = a.template_id
        LEFT JOIN rcsa_responses r ON r.assessment_id = a.id AND r.question_id = q.id
        WHERE 1=1
    """
    
    params = {"skip": skip, "limit": limit}
    
    if status:
        query += " AND a.status = :status"
        params["status"] = status
    
    if department_id:
        query += " AND a.department_id = :department_id"
        params["department_id"] = department_id
    
    if assigned_to:
        query += " AND a.assigned_to = :assigned_to"
        params["assigned_to"] = assigned_to
    
    if period:
        query += " AND a.assessment_period = :period"
        params["period"] = period
    
    if overdue_only:
        query += " AND a.due_date < CURRENT_DATE AND a.status NOT IN ('completed', 'cancelled')"
    
    query += """
        GROUP BY a.id, t.name, ou.unit_name, u.full_name, approver.full_name
        ORDER BY a.due_date ASC
        LIMIT :limit OFFSET :skip
    """
    
    result = db.execute(query, params)
    return [dict(row) for row in result]

@router.get("/assessments/{assessment_id}", response_model=Dict[str, Any])
def get_rcsa_assessment(
    assessment_id: int,
    include_responses: bool = Query(True),
    include_actions: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed RCSA assessment information"""
    
    query = """
        SELECT 
            a.*,
            t.name as template_name,
            ou.unit_name as department_name,
            u.full_name as assigned_to_name
        FROM rcsa_assessments a
        JOIN rcsa_templates t ON a.template_id = t.id
        LEFT JOIN organizational_units ou ON a.department_id = ou.id
        LEFT JOIN users u ON a.assigned_to = u.id
        WHERE a.id = :assessment_id
    """
    
    result = db.execute(query, {"assessment_id": assessment_id}).first()
    if not result:
        raise HTTPException(status_code=404, detail="RCSA assessment not found")
    
    assessment = dict(result)
    
    if include_responses:
        responses_query = """
            SELECT 
                r.*,
                q.question_text,
                q.question_type,
                q.category
            FROM rcsa_responses r
            JOIN rcsa_questions q ON r.question_id = q.id
            WHERE r.assessment_id = :assessment_id
            ORDER BY q.category, q.id
        """
        responses = db.execute(responses_query, {"assessment_id": assessment_id})
        assessment['responses'] = [dict(r) for r in responses]
    
    if include_actions:
        actions_query = """
            SELECT 
                ai.*,
                u.full_name as assigned_to_name
            FROM rcsa_action_items ai
            LEFT JOIN users u ON ai.assigned_to = u.id
            WHERE ai.assessment_id = :assessment_id
            ORDER BY ai.priority DESC, ai.due_date ASC
        """
        actions = db.execute(actions_query, {"assessment_id": assessment_id})
        assessment['action_items'] = [dict(a) for a in actions]
    
    return assessment

@router.post("/assessments", response_model=RCSAAssessmentResponse, status_code=status.HTTP_201_CREATED)
def create_rcsa_assessment(
    assessment: RCSAAssessmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new RCSA assessment"""
    
    # Verify template exists and is active
    template = db.execute(
        "SELECT id FROM rcsa_templates WHERE id = :id AND is_active = true",
        {"id": assessment.template_id}
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Active RCSA template not found")
    
    query = """
        INSERT INTO rcsa_assessments 
        (template_id, department_id, assessment_period, scheduled_date, due_date,
         assigned_to, status, created_at, updated_at)
        VALUES (:template_id, :department_id, :assessment_period, :scheduled_date, :due_date,
                :assigned_to, 'draft', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        RETURNING *
    """
    
    result = db.execute(query, assessment.dict()).first()
    db.commit()
    
    # Send notification to assigned user
    notification_query = """
        INSERT INTO notifications 
        (user_id, type, title, message, created_at)
        VALUES (:user_id, 'RCSA_ASSIGNED', :title, :message, CURRENT_TIMESTAMP)
    """
    
    db.execute(notification_query, {
        "user_id": assessment.assigned_to,
        "title": "New RCSA Assessment Assigned",
        "message": f"You have been assigned an RCSA assessment for period {assessment.assessment_period}"
    })
    db.commit()
    
    return dict(result)

@router.put("/assessments/{assessment_id}/status")
def update_assessment_status(
    assessment_id: int,
    status: AssessmentStatus = Body(...),
    comments: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update RCSA assessment status"""
    
    # Get current assessment
    assessment = db.execute(
        "SELECT * FROM rcsa_assessments WHERE id = :id",
        {"id": assessment_id}
    ).first()
    
    if not assessment:
        raise HTTPException(status_code=404, detail="RCSA assessment not found")
    
    # Validate status transition
    valid_transitions = {
        "draft": ["in_progress", "cancelled"],
        "in_progress": ["under_review", "draft", "cancelled"],
        "under_review": ["approved", "in_progress"],
        "approved": ["completed"],
        "completed": [],
        "cancelled": ["draft"]
    }
    
    if status not in valid_transitions.get(assessment['status'], []):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition from {assessment['status']} to {status}"
        )
    
    update_fields = {"status": status, "updated_at": datetime.now()}
    
    if status == "under_review":
        update_fields["submitted_at"] = datetime.now()
    elif status == "approved":
        update_fields["approved_at"] = datetime.now()
        update_fields["approved_by"] = current_user.id
    
    query = """
        UPDATE rcsa_assessments 
        SET status = :status, updated_at = :updated_at
    """
    
    if status == "under_review":
        query += ", submitted_at = :submitted_at"
    elif status == "approved":
        query += ", approved_at = :approved_at, approved_by = :approved_by"
    
    query += " WHERE id = :assessment_id RETURNING *"
    
    update_fields["assessment_id"] = assessment_id
    result = db.execute(query, update_fields).first()
    
    # Log status change
    log_query = """
        INSERT INTO rcsa_status_history 
        (assessment_id, from_status, to_status, changed_by, comments, created_at)
        VALUES (:assessment_id, :from_status, :to_status, :changed_by, :comments, CURRENT_TIMESTAMP)
    """
    
    db.execute(log_query, {
        "assessment_id": assessment_id,
        "from_status": assessment['status'],
        "to_status": status,
        "changed_by": current_user.id,
        "comments": comments
    })
    
    db.commit()
    
    return {"message": f"Assessment status updated to {status}", "assessment": dict(result)}

@router.post("/assessments/{assessment_id}/responses", status_code=status.HTTP_201_CREATED)
def submit_assessment_responses(
    assessment_id: int,
    responses: List[RCSAResponseBase],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Submit responses for an RCSA assessment"""
    
    # Verify assessment exists and is in progress
    assessment = db.execute(
        "SELECT * FROM rcsa_assessments WHERE id = :id AND status IN ('draft', 'in_progress')",
        {"id": assessment_id}
    ).first()
    
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found or not editable")
    
    # Update assessment status if draft
    if assessment['status'] == 'draft':
        db.execute(
            "UPDATE rcsa_assessments SET status = 'in_progress' WHERE id = :id",
            {"id": assessment_id}
        )
    
    inserted_count = 0
    for response in responses:
        # Check if response already exists
        existing = db.execute(
            "SELECT id FROM rcsa_responses WHERE assessment_id = :aid AND question_id = :qid",
            {"aid": assessment_id, "qid": response.question_id}
        ).first()
        
        if existing:
            # Update existing response
            query = """
                UPDATE rcsa_responses 
                SET response_value = :response_value, response_score = :response_score,
                    comments = :comments, evidence_url = :evidence_url,
                    responded_by = :responded_by, responded_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """
            params = response.dict()
            params['id'] = existing['id']
            params['responded_by'] = current_user.id
        else:
            # Insert new response
            query = """
                INSERT INTO rcsa_responses 
                (assessment_id, question_id, response_value, response_score,
                 comments, evidence_url, responded_by, responded_at)
                VALUES (:assessment_id, :question_id, :response_value, :response_score,
                        :comments, :evidence_url, :responded_by, CURRENT_TIMESTAMP)
            """
            params = response.dict()
            params['responded_by'] = current_user.id
        
        db.execute(query, params)
        inserted_count += 1
    
    # Calculate and update risk score
    risk_score_query = """
        UPDATE rcsa_assessments 
        SET risk_score = (
            SELECT AVG(r.response_score) 
            FROM rcsa_responses r 
            WHERE r.assessment_id = :assessment_id
        )
        WHERE id = :assessment_id
    """
    
    db.execute(risk_score_query, {"assessment_id": assessment_id})
    db.commit()
    
    return {
        "message": f"Submitted {inserted_count} responses",
        "assessment_id": assessment_id
    }

@router.post("/assessments/{assessment_id}/actions", status_code=status.HTTP_201_CREATED)
def create_action_items(
    assessment_id: int,
    actions: List[RCSAActionItemBase],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create action items from RCSA assessment"""
    
    # Verify assessment exists
    assessment = db.execute(
        "SELECT id FROM rcsa_assessments WHERE id = :id",
        {"id": assessment_id}
    ).first()
    
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    inserted_ids = []
    for action in actions:
        query = """
            INSERT INTO rcsa_action_items 
            (assessment_id, identified_issue, recommended_action, priority,
             assigned_to, due_date, estimated_cost, business_impact, status, created_by, created_at)
            VALUES (:assessment_id, :identified_issue, :recommended_action, :priority,
                    :assigned_to, :due_date, :estimated_cost, :business_impact, 'open', :created_by, CURRENT_TIMESTAMP)
            RETURNING id
        """
        
        params = action.dict()
        params['created_by'] = current_user.id
        
        result = db.execute(query, params).first()
        inserted_ids.append(result['id'])
    
    db.commit()
    
    return {
        "message": f"Created {len(actions)} action items",
        "action_ids": inserted_ids
    }

@router.get("/schedule", response_model=List[Dict[str, Any]])
def get_rcsa_schedule(
    year: int = Query(datetime.now().year),
    department_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get RCSA assessment schedule for the year"""
    
    query = """
        SELECT 
            s.*,
            t.name as template_name,
            ou.unit_name as department_name,
            COUNT(a.id) as assessments_created
        FROM rcsa_schedule s
        JOIN rcsa_templates t ON s.template_id = t.id
        LEFT JOIN organizational_units ou ON s.department_id = ou.id
        LEFT JOIN rcsa_assessments a ON a.template_id = s.template_id 
            AND a.department_id = s.department_id
            AND EXTRACT(YEAR FROM a.scheduled_date) = :year
        WHERE EXTRACT(YEAR FROM s.scheduled_date) = :year
    """
    
    params = {"year": year}
    
    if department_id:
        query += " AND s.department_id = :department_id"
        params["department_id"] = department_id
    
    query += """
        GROUP BY s.id, t.name, ou.unit_name
        ORDER BY s.scheduled_date
    """
    
    result = db.execute(query, params)
    return [dict(row) for row in result]

@router.post("/schedule/generate")
def generate_rcsa_schedule(
    year: int = Body(...),
    template_ids: List[int] = Body(...),
    department_ids: List[int] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate RCSA assessment schedule for the year"""
    
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to generate schedule")
    
    created_count = 0
    
    for template_id in template_ids:
        # Get template frequency
        template = db.execute(
            "SELECT frequency FROM rcsa_templates WHERE id = :id",
            {"id": template_id}
        ).first()
        
        if not template:
            continue
        
        # Determine assessment periods based on frequency
        periods = []
        if template['frequency'] == 'monthly':
            periods = [f"{year}-{str(i).zfill(2)}" for i in range(1, 13)]
        elif template['frequency'] == 'quarterly':
            periods = [f"{year}-Q1", f"{year}-Q2", f"{year}-Q3", f"{year}-Q4"]
        elif template['frequency'] == 'semi-annually':
            periods = [f"{year}-H1", f"{year}-H2"]
        elif template['frequency'] == 'annually':
            periods = [f"{year}"]
        
        for department_id in department_ids:
            for i, period in enumerate(periods):
                # Calculate scheduled date
                if template['frequency'] == 'monthly':
                    scheduled_date = date(year, i + 1, 1)
                    due_date = date(year, i + 1, 28)
                elif template['frequency'] == 'quarterly':
                    scheduled_date = date(year, (i * 3) + 1, 1)
                    due_date = date(year, (i * 3) + 3, 31 if (i * 3) + 3 in [3, 5, 7, 8, 10, 12] else 30)
                elif template['frequency'] == 'semi-annually':
                    scheduled_date = date(year, (i * 6) + 1, 1)
                    due_date = date(year, (i * 6) + 6, 30)
                else:  # annually
                    scheduled_date = date(year, 1, 1)
                    due_date = date(year, 12, 31)
                
                # Insert schedule entry
                query = """
                    INSERT INTO rcsa_schedule 
                    (template_id, department_id, assessment_period, scheduled_date, due_date, created_at)
                    VALUES (:template_id, :department_id, :assessment_period, :scheduled_date, :due_date, CURRENT_TIMESTAMP)
                    ON CONFLICT (template_id, department_id, assessment_period) DO NOTHING
                """
                
                db.execute(query, {
                    "template_id": template_id,
                    "department_id": department_id,
                    "assessment_period": period,
                    "scheduled_date": scheduled_date,
                    "due_date": due_date
                })
                
                created_count += 1
    
    db.commit()
    
    return {
        "message": f"Generated {created_count} schedule entries for year {year}",
        "year": year
    }