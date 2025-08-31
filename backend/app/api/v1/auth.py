from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import or_
import logging

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.models.user import User
from app.schemas.user import Token

# Import AD integration if enabled
if settings.AD_ENABLED:
    from app.core.ad_integration import authenticate_with_ad, get_ad_client

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    username: str = Form(),
    password: str = Form()
) -> Token:
    """OAuth2 compatible token login - supports local, AD, or hybrid authentication"""
    
    auth_success = False
    user = None
    ad_auth_result = None
    
    # Determine authentication method based on settings
    if settings.AUTH_MODE == "ad":
        # AD-only authentication
        if settings.AD_ENABLED:
            ad_auth_result = authenticate_with_ad(username, password, db)
            if ad_auth_result:
                return Token(
                    access_token=ad_auth_result["access_token"],
                    token_type="bearer"
                )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="AD authentication failed or not configured",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    elif settings.AUTH_MODE == "hybrid":
        # Try AD first, then fall back to local
        if settings.AD_ENABLED:
            try:
                ad_auth_result = authenticate_with_ad(username, password, db)
                if ad_auth_result:
                    return Token(
                        access_token=ad_auth_result["access_token"],
                        token_type="bearer"
                    )
            except Exception as e:
                logger.warning(f"AD authentication failed, trying local auth: {e}")
        
        # Fall back to local authentication
        user = db.query(User).filter(
            or_(
                User.email == username,
                User.username == username
            )
        ).first()
        
        if user and verify_password(password, user.hashed_password):
            auth_success = True
    
    else:  # Local authentication only
        user = db.query(User).filter(
            or_(
                User.email == username,
                User.username == username
            )
        ).first()
        
        if user and verify_password(password, user.hashed_password):
            auth_success = True
    
    # Handle local authentication result
    if not auth_success or not user:
        # Update failed login attempts if user exists
        if user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                user.is_active = False
            db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account locked until {user.locked_until}"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Update last_login and reset failed attempts
    try:
        user.last_login = datetime.utcnow()
        user.last_activity = datetime.utcnow()
        user.failed_login_attempts = 0
        user.locked_until = None
        if not user.is_active:
            user.is_active = True
        db.commit()
    except Exception as e:
        logger.error(f"Error updating user login info: {e}")
        db.rollback()
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.email,
            "username": user.username,
            "user_id": str(user.id),
            "role": user.role.value if hasattr(user, 'role') else "viewer",
            "department": user.department if hasattr(user, 'department') else None
        },
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")

@router.post("/logout")
def logout():
    """Logout endpoint (client should discard token)"""
    return {"message": "Successfully logged out"}
