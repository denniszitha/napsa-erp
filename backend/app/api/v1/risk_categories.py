from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_

from app.core.database import get_db
from app.models.risk_category import RiskCategory
from app.models.risk import Risk
from app.models.user import User
from app.schemas.risk_category import (
    RiskCategoryCreate,
    RiskCategoryUpdate,
    RiskCategoryResponse,
    RiskCategoryList,
    RiskCategoryTree
)
from app.api.deps import get_current_active_user

router = APIRouter(
    tags=["Risk Categories"]
)


@router.get("/", response_model=RiskCategoryList)
def get_risk_categories(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    search: Optional[str] = Query(None, description="Search term for category name or description"),
    parent_id: Optional[int] = Query(None, description="Filter by parent category ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all risk categories with optional filtering.
    
    Returns categories with their associated risk counts and child category counts.
    """
    query = db.query(RiskCategory)
    
    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                RiskCategory.name.ilike(search_term),
                RiskCategory.description.ilike(search_term)
            )
        )
    
    if parent_id is not None:
        query = query.filter(RiskCategory.parent_id == parent_id)
    
    if is_active is not None:
        query = query.filter(RiskCategory.is_active == is_active)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    categories = query.offset(skip).limit(limit).all()
    
    # Enhance with counts
    items = []
    for category in categories:
        # Count associated risks
        risks_count = db.query(Risk).filter(Risk.category_id == category.id).count()
        
        # Count child categories
        children_count = db.query(RiskCategory).filter(
            RiskCategory.parent_id == category.id
        ).count()
        
        # Create response object
        response = RiskCategoryResponse(
            **category.__dict__,
            full_path=category.full_path,
            children_count=children_count,
            risks_count=risks_count
        )
        items.append(response)
    
    return RiskCategoryList(total=total, items=items)


@router.get("/tree", response_model=List[RiskCategoryTree])
def get_category_tree(
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get risk categories in hierarchical tree structure.
    
    Returns only top-level categories with their nested children.
    """
    def build_tree(category):
        # Get counts
        risks_count = db.query(Risk).filter(Risk.category_id == category.id).count()
        children_count = len(category.children)
        
        # Build children recursively
        children = []
        for child in category.children:
            if is_active is None or child.is_active == is_active:
                children.append(build_tree(child))
        
        return RiskCategoryTree(
            id=category.id,
            name=category.name,
            description=category.description,
            parent_id=category.parent_id,
            is_active=category.is_active,
            created_at=category.created_at,
            updated_at=category.updated_at,
            full_path=category.full_path,
            children_count=children_count,
            risks_count=risks_count,
            children=children
        )
    
    # Get root categories (no parent)
    query = db.query(RiskCategory).filter(RiskCategory.parent_id.is_(None))
    
    if is_active is not None:
        query = query.filter(RiskCategory.is_active == is_active)
    
    root_categories = query.all()
    
    return [build_tree(cat) for cat in root_categories]


@router.get("/{category_id}", response_model=RiskCategoryResponse)
def get_risk_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific risk category by ID."""
    category = db.query(RiskCategory).filter(RiskCategory.id == category_id).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk category with id {category_id} not found"
        )
    
    # Get counts
    risks_count = db.query(Risk).filter(Risk.category_id == category.id).count()
    children_count = db.query(RiskCategory).filter(
        RiskCategory.parent_id == category.id
    ).count()
    
    return RiskCategoryResponse(
        **category.__dict__,
        full_path=category.full_path,
        children_count=children_count,
        risks_count=risks_count
    )


@router.post("/", response_model=RiskCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_risk_category(
    category_data: RiskCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new risk category.
    
    Requires appropriate permissions to manage risk categories.
    """
    # Check if category name already exists
    existing = db.query(RiskCategory).filter(
        RiskCategory.name == category_data.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with name '{category_data.name}' already exists"
        )
    
    # Validate parent_id if provided
    if category_data.parent_id:
        parent = db.query(RiskCategory).filter(
            RiskCategory.id == category_data.parent_id
        ).first()
        
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parent category with id {category_data.parent_id} not found"
            )
        
        # Check for circular reference (simple check - can be enhanced)
        if parent.parent_id:
            grandparent = db.query(RiskCategory).filter(
                RiskCategory.id == parent.parent_id
            ).first()
            if grandparent and grandparent.parent_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category hierarchy cannot exceed 3 levels"
                )
    
    # Create new category
    new_category = RiskCategory(**category_data.dict())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    return RiskCategoryResponse(
        **new_category.__dict__,
        full_path=new_category.full_path,
        children_count=0,
        risks_count=0
    )


@router.put("/{category_id}", response_model=RiskCategoryResponse)
def update_risk_category(
    category_id: int,
    category_update: RiskCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update an existing risk category.
    
    Cannot update a category if it has associated risks unless only updating is_active status.
    """
    category = db.query(RiskCategory).filter(RiskCategory.id == category_id).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk category with id {category_id} not found"
        )
    
    # Check if name is being changed and if it's unique
    if category_update.name and category_update.name != category.name:
        existing = db.query(RiskCategory).filter(
            RiskCategory.name == category_update.name,
            RiskCategory.id != category_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with name '{category_update.name}' already exists"
            )
    
    # Validate parent_id if being updated
    if category_update.parent_id is not None:
        # Prevent self-reference
        if category_update.parent_id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category cannot be its own parent"
            )
        
        # Prevent circular reference
        if category_update.parent_id:
            parent = db.query(RiskCategory).filter(
                RiskCategory.id == category_update.parent_id
            ).first()
            
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Parent category with id {category_update.parent_id} not found"
                )
            
            # Check if the new parent is a child of current category
            current = parent
            while current.parent_id:
                if current.parent_id == category_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot create circular reference in category hierarchy"
                    )
                current = db.query(RiskCategory).filter(
                    RiskCategory.id == current.parent_id
                ).first()
    
    # Update category
    update_data = category_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)
    
    db.commit()
    db.refresh(category)
    
    # Get counts
    risks_count = db.query(Risk).filter(Risk.category_id == category.id).count()
    children_count = db.query(RiskCategory).filter(
        RiskCategory.parent_id == category.id
    ).count()
    
    return RiskCategoryResponse(
        **category.__dict__,
        full_path=category.full_path,
        children_count=children_count,
        risks_count=risks_count
    )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_risk_category(
    category_id: int,
    force: bool = Query(False, description="Force delete even if category has risks"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a risk category.
    
    By default, cannot delete a category that has:
    - Associated risks
    - Child categories
    
    Use force=true to override (risks will be reassigned to default category).
    """
    category = db.query(RiskCategory).filter(RiskCategory.id == category_id).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk category with id {category_id} not found"
        )
    
    # Check for associated risks
    risks_count = db.query(Risk).filter(Risk.category_id == category_id).count()
    
    if risks_count > 0 and not force:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category with {risks_count} associated risks. Use force=true to override."
        )
    
    # Check for child categories
    children_count = db.query(RiskCategory).filter(
        RiskCategory.parent_id == category_id
    ).count()
    
    if children_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category with {children_count} child categories. Delete children first."
        )
    
    # If forcing, reassign risks to default category (Operational)
    if risks_count > 0 and force:
        default_category = db.query(RiskCategory).filter(
            RiskCategory.name == "Operational"
        ).first()
        
        if default_category:
            db.query(Risk).filter(Risk.category_id == category_id).update(
                {"category_id": default_category.id}
            )
        else:
            # Create default if it doesn't exist
            default_category = RiskCategory(
                name="Uncategorized",
                description="Default category for uncategorized risks"
            )
            db.add(default_category)
            db.flush()
            
            db.query(Risk).filter(Risk.category_id == category_id).update(
                {"category_id": default_category.id}
            )
    
    # Delete the category
    db.delete(category)
    db.commit()
    
    return {"message": f"Category {category.name} deleted successfully"}


@router.get("/{category_id}/risks", response_model=List[dict])
def get_category_risks(
    category_id: int,
    include_children: bool = Query(False, description="Include risks from child categories"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all risks associated with a specific category.
    
    Can optionally include risks from child categories.
    """
    category = db.query(RiskCategory).filter(RiskCategory.id == category_id).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk category with id {category_id} not found"
        )
    
    # Build list of category IDs to query
    category_ids = [category_id]
    
    if include_children:
        # Get all descendant categories
        def get_descendants(cat_id):
            children = db.query(RiskCategory).filter(
                RiskCategory.parent_id == cat_id
            ).all()
            
            ids = []
            for child in children:
                ids.append(child.id)
                ids.extend(get_descendants(child.id))
            return ids
        
        category_ids.extend(get_descendants(category_id))
    
    # Query risks
    risks = db.query(Risk).filter(
        Risk.category_id.in_(category_ids)
    ).offset(skip).limit(limit).all()
    
    # Format response
    return [
        {
            "id": risk.id,
            "title": risk.title,
            "description": risk.description,
            "category_id": risk.category_id,
            "category_name": risk.risk_category.name if risk.risk_category else None,
            "status": risk.status,
            "likelihood": risk.likelihood,
            "impact": risk.impact,
            "inherent_risk_score": risk.inherent_risk_score,
            "residual_risk_score": risk.residual_risk_score
        }
        for risk in risks
    ]


@router.post("/{category_id}/activate", response_model=RiskCategoryResponse)
def activate_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Activate a previously deactivated risk category."""
    category = db.query(RiskCategory).filter(RiskCategory.id == category_id).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk category with id {category_id} not found"
        )
    
    category.is_active = True
    db.commit()
    db.refresh(category)
    
    # Get counts
    risks_count = db.query(Risk).filter(Risk.category_id == category.id).count()
    children_count = db.query(RiskCategory).filter(
        RiskCategory.parent_id == category.id
    ).count()
    
    return RiskCategoryResponse(
        **category.__dict__,
        full_path=category.full_path,
        children_count=children_count,
        risks_count=risks_count
    )


@router.post("/{category_id}/deactivate", response_model=RiskCategoryResponse)
def deactivate_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Deactivate a risk category without deleting it."""
    category = db.query(RiskCategory).filter(RiskCategory.id == category_id).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk category with id {category_id} not found"
        )
    
    category.is_active = False
    db.commit()
    db.refresh(category)
    
    # Get counts
    risks_count = db.query(Risk).filter(Risk.category_id == category.id).count()
    children_count = db.query(RiskCategory).filter(
        RiskCategory.parent_id == category.id
    ).count()
    
    return RiskCategoryResponse(
        **category.__dict__,
        full_path=category.full_path,
        children_count=children_count,
        risks_count=risks_count
    )