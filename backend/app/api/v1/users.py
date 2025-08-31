from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.base import PaginatedResponse
from app.core.security import get_password_hash

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all users"""
    users = db.query(User).offset(skip).limit(limit).all()
    return [UserResponse.model_validate(user) for user in users]

@router.get("/me", response_model=UserResponse)
def read_current_user(
    current_user: User = Depends(get_current_active_user),
):
    """Get current user"""
    return UserResponse.model_validate(current_user)

@router.post("/", response_model=UserResponse)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    """Create new user (temporary - no auth required for initial setup)"""
    # Check if user exists
    if db.query(User).filter(
        (User.email == user_in.email) | (User.username == user_in.username)
    ).first():
        raise HTTPException(
            status_code=400,
            detail="User with this email or username already exists"
        )
    
    # Create user
    user = User(
        **user_in.model_dump(exclude={"password"}),
        hashed_password=get_password_hash(user_in.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserResponse.model_validate(user)

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if email is being changed and already exists
    if user_in.email and user_in.email != user.email:
        existing_user = db.query(User).filter(User.email == user_in.email).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists"
            )
    
    # Update user fields
    update_data = user_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return UserResponse.model_validate(user)

@router.delete("/{user_id}")
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete your own user account"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}

@router.get("/test-assessment")
def test_assessment():
    """Test endpoint in users router"""
    return {"message": "This is a test endpoint in users router to verify routing works"}

# Remove test endpoints and add clean up
pass
