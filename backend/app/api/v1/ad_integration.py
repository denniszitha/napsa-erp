"""
Active Directory Integration API Endpoints
Provides endpoints for AD synchronization, testing, and management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.api.deps import get_db, get_current_active_user
from app.models.user import User, UserRole
from app.core.config import settings

# Only import AD integration if enabled
if settings.AD_ENABLED:
    from app.core.ad_integration import (
        get_ad_client,
        ActiveDirectoryClient,
        ADUser
    )

logger = logging.getLogger(__name__)
router = APIRouter()


def require_admin(current_user: User = Depends(get_current_active_user)):
    """Require admin role for AD management endpoints"""
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


@router.get("/status")
def get_ad_status(current_user: User = Depends(get_current_active_user)):
    """Get current AD integration status and configuration"""
    return {
        "enabled": settings.AD_ENABLED,
        "auth_mode": settings.AUTH_MODE,
        "server": settings.AD_SERVER_URL if settings.AD_ENABLED else None,
        "domain": settings.AD_DOMAIN if settings.AD_ENABLED else None,
        "base_dn": settings.AD_BASE_DN if settings.AD_ENABLED else None,
        "sync_enabled": settings.AD_SYNC_ENABLED,
        "sync_interval_hours": settings.AD_SYNC_INTERVAL_HOURS,
        "ssl_enabled": settings.AD_USE_SSL if settings.AD_ENABLED else None
    }


@router.post("/test-connection")
def test_ad_connection(current_user: User = Depends(require_admin)):
    """Test AD connection and return diagnostic information"""
    if not settings.AD_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AD integration is not enabled"
        )
    
    try:
        ad_client = get_ad_client()
        result = ad_client.test_connection()
        
        if not result["connected"]:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"AD connection failed: {result.get('error', 'Unknown error')}"
            )
        
        return result
    
    except Exception as e:
        logger.error(f"Error testing AD connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/sync-users")
def sync_ad_users(
    background_tasks: BackgroundTasks,
    department: Optional[str] = Query(None, description="Filter by department"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Synchronize users from Active Directory"""
    if not settings.AD_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AD integration is not enabled"
        )
    
    def run_sync():
        """Background task for user synchronization"""
        try:
            ad_client = get_ad_client()
            stats = ad_client.sync_users(db, department_filter=department)
            logger.info(f"AD sync completed: {stats}")
        except Exception as e:
            logger.error(f"AD sync failed: {e}")
    
    # Run sync in background
    background_tasks.add_task(run_sync)
    
    return {
        "message": "User synchronization started",
        "department_filter": department,
        "timestamp": datetime.utcnow()
    }


@router.get("/sync-status")
def get_sync_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get the status of the last AD synchronization"""
    # In production, this would query a sync status table
    # For now, return basic stats
    
    total_users = db.query(User).count()
    ad_users = db.query(User).filter(
        User.username.like('%@%')  # Simple check for AD users
    ).count()
    
    return {
        "total_users": total_users,
        "ad_synced_users": ad_users,
        "local_users": total_users - ad_users,
        "last_sync": None,  # Would be stored in database
        "sync_enabled": settings.AD_SYNC_ENABLED
    }


@router.get("/search-users")
def search_ad_users(
    query: str = Query(..., min_length=2, description="Search term"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user)
):
    """Search for users in Active Directory"""
    if not settings.AD_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AD integration is not enabled"
        )
    
    try:
        ad_client = get_ad_client()
        users = ad_client.search_users(query, max_results=limit)
        
        return {
            "count": len(users),
            "users": [
                {
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "department": user.department,
                    "title": user.title,
                    "enabled": user.enabled
                }
                for user in users
            ]
        }
    
    except Exception as e:
        logger.error(f"Error searching AD users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error searching Active Directory"
        )


@router.get("/user/{username}/groups")
def get_user_ad_groups(
    username: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get AD groups for a specific user"""
    if not settings.AD_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AD integration is not enabled"
        )
    
    try:
        ad_client = get_ad_client()
        groups = ad_client.get_user_groups(username)
        
        return {
            "username": username,
            "groups": groups,
            "count": len(groups)
        }
    
    except Exception as e:
        logger.error(f"Error fetching user groups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching AD groups"
        )


@router.get("/group-mappings")
def get_group_role_mappings(current_user: User = Depends(require_admin)):
    """Get current AD group to role mappings"""
    if not settings.AD_ENABLED:
        return {"enabled": False, "mappings": {}}
    
    try:
        ad_client = get_ad_client()
        mappings = ad_client.config.group_role_mapping
        
        return {
            "enabled": True,
            "mappings": {
                group_dn: role.value
                for group_dn, role in mappings.items()
            }
        }
    
    except Exception as e:
        logger.error(f"Error fetching group mappings: {e}")
        return {"enabled": True, "mappings": {}, "error": str(e)}


@router.post("/import-user")
def import_ad_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Import a specific user from Active Directory"""
    if not settings.AD_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AD integration is not enabled"
        )
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            User.username == username
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists in the system"
            )
        
        # Fetch user from AD
        ad_client = get_ad_client()
        ad_user = ad_client.get_user_details(username)
        
        if not ad_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in Active Directory"
            )
        
        # Sync the user
        result = ad_client._sync_single_user(db, ad_user)
        
        return {
            "message": f"User {username} imported successfully",
            "action": result,
            "user": {
                "username": ad_user.username,
                "email": ad_user.email,
                "full_name": ad_user.full_name,
                "department": ad_user.department,
                "role": ad_client._determine_user_role(ad_user.groups).value
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing AD user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/validate-credentials")
def validate_ad_credentials(
    username: str,
    password: str,
    current_user: User = Depends(require_admin)
):
    """Validate AD credentials without creating a session"""
    if not settings.AD_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AD integration is not enabled"
        )
    
    try:
        ad_client = get_ad_client()
        success, ad_user = ad_client.authenticate_user(username, password)
        
        if success:
            return {
                "valid": True,
                "user": {
                    "username": ad_user.username,
                    "email": ad_user.email,
                    "full_name": ad_user.full_name,
                    "department": ad_user.department,
                    "enabled": ad_user.enabled
                }
            }
        else:
            return {
                "valid": False,
                "message": "Invalid credentials"
            }
    
    except Exception as e:
        logger.error(f"Error validating AD credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error validating credentials"
        )


@router.get("/departments")
def get_ad_departments(
    current_user: User = Depends(get_current_active_user)
):
    """Get list of unique departments from AD users in the system"""
    if not settings.AD_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AD integration is not enabled"
        )
    
    try:
        # This would typically query AD directly for all departments
        # For now, return departments from synced users
        db = next(get_db())
        departments = db.query(User.department).distinct().filter(
            User.department.isnot(None)
        ).all()
        
        return {
            "departments": [dept[0] for dept in departments if dept[0]],
            "count": len(departments)
        }
    
    except Exception as e:
        logger.error(f"Error fetching departments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching departments"
        )