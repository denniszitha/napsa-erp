"""
System Configuration API Endpoints
For managing runtime configuration settings
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import logging

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.system_config import SystemConfiguration
from app.models.enums import UserRole
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic schemas
class SystemConfigBase(BaseModel):
    config_key: str = Field(..., description="Unique configuration key")
    config_value: str = Field(..., description="Configuration value")
    config_type: str = Field(default="string", description="Data type: string, integer, boolean, json, float")
    category: Optional[str] = Field(None, description="Configuration category")
    display_name: Optional[str] = Field(None, description="Display name for UI")
    description: Optional[str] = Field(None, description="Configuration description")
    is_sensitive: bool = Field(default=False, description="Whether value should be encrypted")
    validation_rules: Optional[dict] = Field(None, description="JSON schema for validation")
    default_value: Optional[str] = Field(None, description="Default value")
    requires_restart: bool = Field(default=False, description="Whether change requires restart")


class SystemConfigCreate(SystemConfigBase):
    pass


class SystemConfigUpdate(BaseModel):
    config_value: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SystemConfigResponse(SystemConfigBase):
    id: int
    is_active: bool
    created_at: str
    updated_at: Optional[str]
    
    class Config:
        from_attributes = True


def require_admin(current_user: User = Depends(get_current_active_user)):
    """Require admin role for system configuration"""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


@router.get("/", response_model=List[SystemConfigResponse])
def get_configurations(
    category: Optional[str] = Query(None, description="Filter by category"),
    active_only: bool = Query(True, description="Show only active configurations"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all system configurations"""
    query = db.query(SystemConfiguration)
    
    if category:
        query = query.filter(SystemConfiguration.category == category)
    
    if active_only:
        query = query.filter(SystemConfiguration.is_active == True)
    
    # Hide sensitive values for non-admins
    configs = query.all()
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        for config in configs:
            if config.is_sensitive:
                config.config_value = "***HIDDEN***"
    
    return configs


@router.get("/categories", response_model=List[str])
def get_configuration_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all configuration categories"""
    categories = db.query(SystemConfiguration.category).distinct().all()
    return [cat[0] for cat in categories if cat[0]]


@router.get("/{config_key}", response_model=SystemConfigResponse)
def get_configuration(
    config_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get specific configuration by key"""
    config = db.query(SystemConfiguration).filter(
        SystemConfiguration.config_key == config_key
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration '{config_key}' not found"
        )
    
    # Hide sensitive value for non-admins
    if config.is_sensitive and current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        config.config_value = "***HIDDEN***"
    
    return config


@router.get("/{config_key}/value")
def get_configuration_value(
    config_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get typed configuration value"""
    config = db.query(SystemConfiguration).filter(
        SystemConfiguration.config_key == config_key,
        SystemConfiguration.is_active == True
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active configuration '{config_key}' not found"
        )
    
    # Check permissions for sensitive configs
    if config.is_sensitive and current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges to access sensitive configuration"
        )
    
    return {
        "key": config_key,
        "value": config.typed_value,
        "type": config.config_type
    }


@router.post("/", response_model=SystemConfigResponse)
def create_configuration(
    config_data: SystemConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create new system configuration"""
    # Check if key already exists
    existing = db.query(SystemConfiguration).filter(
        SystemConfiguration.config_key == config_data.config_key
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Configuration key '{config_data.config_key}' already exists"
        )
    
    # Validate value against type
    try:
        if config_data.config_type == 'integer':
            int(config_data.config_value)
        elif config_data.config_type == 'float':
            float(config_data.config_value)
        elif config_data.config_type == 'boolean':
            if config_data.config_value.lower() not in ('true', 'false', '1', '0', 'yes', 'no'):
                raise ValueError("Invalid boolean value")
        elif config_data.config_type == 'json':
            json.loads(config_data.config_value)
    except (ValueError, json.JSONDecodeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid value for type {config_data.config_type}: {str(e)}"
        )
    
    # Create configuration
    config = SystemConfiguration(
        **config_data.dict(),
        created_by_id=current_user.id,
        is_active=True
    )
    
    db.add(config)
    db.commit()
    db.refresh(config)
    
    logger.info(f"Configuration '{config.config_key}' created by {current_user.username}")
    
    return config


@router.put("/{config_key}", response_model=SystemConfigResponse)
def update_configuration(
    config_key: str,
    config_update: SystemConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update system configuration"""
    config = db.query(SystemConfiguration).filter(
        SystemConfiguration.config_key == config_key
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration '{config_key}' not found"
        )
    
    # Validate new value if provided
    if config_update.config_value is not None:
        try:
            if config.config_type == 'integer':
                int(config_update.config_value)
            elif config.config_type == 'float':
                float(config_update.config_value)
            elif config.config_type == 'boolean':
                if config_update.config_value.lower() not in ('true', 'false', '1', '0', 'yes', 'no'):
                    raise ValueError("Invalid boolean value")
            elif config.config_type == 'json':
                json.loads(config_update.config_value)
        except (ValueError, json.JSONDecodeError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid value for type {config.config_type}: {str(e)}"
            )
    
    # Update fields
    update_data = config_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)
    
    config.updated_by_id = current_user.id
    
    db.commit()
    db.refresh(config)
    
    logger.info(f"Configuration '{config_key}' updated by {current_user.username}")
    
    if config.requires_restart:
        logger.warning(f"Configuration '{config_key}' requires system restart to take effect")
    
    return config


@router.delete("/{config_key}")
def delete_configuration(
    config_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete system configuration"""
    config = db.query(SystemConfiguration).filter(
        SystemConfiguration.config_key == config_key
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration '{config_key}' not found"
        )
    
    # Don't delete, just deactivate
    config.is_active = False
    config.updated_by_id = current_user.id
    
    db.commit()
    
    logger.info(f"Configuration '{config_key}' deactivated by {current_user.username}")
    
    return {"message": f"Configuration '{config_key}' deactivated"}


@router.post("/reset/{config_key}")
def reset_configuration_to_default(
    config_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Reset configuration to default value"""
    config = db.query(SystemConfiguration).filter(
        SystemConfiguration.config_key == config_key
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration '{config_key}' not found"
        )
    
    if not config.default_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No default value defined for '{config_key}'"
        )
    
    config.config_value = config.default_value
    config.updated_by_id = current_user.id
    
    db.commit()
    
    logger.info(f"Configuration '{config_key}' reset to default by {current_user.username}")
    
    return {
        "message": f"Configuration '{config_key}' reset to default",
        "default_value": config.default_value
    }


@router.post("/bulk-update")
def bulk_update_configurations(
    updates: List[dict],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update multiple configurations at once"""
    results = []
    errors = []
    
    for update in updates:
        try:
            config = db.query(SystemConfiguration).filter(
                SystemConfiguration.config_key == update.get('config_key')
            ).first()
            
            if config:
                config.config_value = update.get('config_value')
                config.updated_by_id = current_user.id
                results.append({
                    "key": config.config_key,
                    "status": "updated"
                })
            else:
                errors.append({
                    "key": update.get('config_key'),
                    "error": "Not found"
                })
        except Exception as e:
            errors.append({
                "key": update.get('config_key'),
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "updated": len(results),
        "errors": len(errors),
        "results": results,
        "errors_detail": errors
    }