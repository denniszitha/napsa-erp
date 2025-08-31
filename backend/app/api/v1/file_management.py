"""
File Management API Endpoints
For document upload, storage, and retrieval
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import hashlib
import shutil
from datetime import datetime
import mimetypes
import uuid
import json
import logging

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.file_management import File as FileModel, FileCategory
from app.models.enums import FileAccessLevel
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()

# Configuration
UPLOAD_BASE_PATH = os.getenv("UPLOAD_PATH", "/opt/napsa-erm/backend/uploads")
MAX_FILE_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB default

# Pydantic schemas
class FileCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    allowed_extensions: List[str] = Field(default=["pdf", "docx", "xlsx", "png", "jpg"])
    max_file_size: int = Field(default=10485760)
    storage_path: Optional[str] = None
    requires_approval: bool = False
    retention_period_days: Optional[int] = None
    is_sensitive: bool = False
    access_level: Optional[str] = None


class FileCategoryResponse(FileCategoryCreate):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class FileResponse(BaseModel):
    id: int
    category_id: Optional[int]
    original_filename: str
    file_size: int
    file_extension: str
    mime_type: str
    description: Optional[str]
    tags: Optional[List[str]]
    is_public: bool
    access_level: Optional[str]
    uploaded_by_id: int
    uploaded_at: datetime
    related_entity_type: Optional[str]
    related_entity_id: Optional[int]
    
    class Config:
        from_attributes = True


def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """Validate file extension against allowed list"""
    ext = os.path.splitext(filename)[1].lower().replace('.', '')
    return ext in allowed_extensions


def ensure_directory(path: str):
    """Ensure directory exists"""
    os.makedirs(path, exist_ok=True)
    os.chmod(path, 0o755)


@router.get("/categories", response_model=List[FileCategoryResponse])
def get_file_categories(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all file categories"""
    query = db.query(FileCategory)
    if active_only:
        query = query.filter(FileCategory.is_active == True)
    return query.all()


@router.post("/categories", response_model=FileCategoryResponse)
def create_file_category(
    category: FileCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new file category"""
    # Set default storage path if not provided
    if not category.storage_path:
        safe_name = category.name.lower().replace(' ', '_')
        category.storage_path = f"/uploads/{safe_name}"
    
    db_category = FileCategory(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    # Create the directory
    full_path = os.path.join(UPLOAD_BASE_PATH, category.storage_path.lstrip('/'))
    ensure_directory(full_path)
    
    logger.info(f"File category '{category.name}' created by {current_user.username}")
    
    return db_category


@router.post("/upload", response_model=FileResponse)
async def upload_file(
    file: UploadFile = File(...),
    category_id: int = Form(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # JSON string of tags
    is_public: bool = Form(False),
    access_level: Optional[str] = Form(None),
    related_entity_type: Optional[str] = Form(None),
    related_entity_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload a file"""
    # Get category
    category = db.query(FileCategory).filter(FileCategory.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File category not found"
        )
    
    # Validate file size
    if file.size > category.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {category.max_file_size} bytes"
        )
    
    # Validate file extension
    if not validate_file_extension(file.filename, category.allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type not allowed. Allowed extensions: {category.allowed_extensions}"
        )
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    stored_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Determine storage path
    category_path = category.storage_path or f"/uploads/{category.name.lower().replace(' ', '_')}"
    full_directory = os.path.join(UPLOAD_BASE_PATH, category_path.lstrip('/'))
    ensure_directory(full_directory)
    
    file_path = os.path.join(full_directory, stored_filename)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file"
        )
    
    # Calculate file hash
    file_hash = calculate_file_hash(file_path)
    
    # Parse tags if provided
    tags_list = None
    if tags:
        try:
            tags_list = json.loads(tags)
        except json.JSONDecodeError:
            tags_list = tags.split(',')
    
    # Create database record
    db_file = FileModel(
        category_id=category_id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_path=file_path,
        file_size=file.size,
        file_extension=file_extension.replace('.', ''),
        mime_type=file.content_type or mimetypes.guess_type(file.filename)[0],
        file_hash=file_hash,
        description=description,
        tags=tags_list,
        is_public=is_public,
        access_level=access_level,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        uploaded_by_id=current_user.id,
        is_active=True,
        is_processed=False
    )
    
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    logger.info(f"File '{file.filename}' uploaded by {current_user.username}")
    
    return db_file


@router.get("/", response_model=List[FileResponse])
def get_files(
    category_id: Optional[int] = Query(None),
    related_entity_type: Optional[str] = Query(None),
    related_entity_id: Optional[int] = Query(None),
    uploaded_by_me: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get files with filtering"""
    query = db.query(FileModel).filter(FileModel.is_active == True)
    
    if category_id:
        query = query.filter(FileModel.category_id == category_id)
    
    if related_entity_type:
        query = query.filter(FileModel.related_entity_type == related_entity_type)
    
    if related_entity_id:
        query = query.filter(FileModel.related_entity_id == related_entity_id)
    
    if uploaded_by_me:
        query = query.filter(FileModel.uploaded_by_id == current_user.id)
    
    # Filter by access level
    if not current_user.is_superuser:
        query = query.filter(
            (FileModel.is_public == True) |
            (FileModel.uploaded_by_id == current_user.id)
        )
    
    return query.offset(skip).limit(limit).all()


@router.get("/{file_id}", response_model=FileResponse)
def get_file_info(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get file information"""
    file_record = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.is_active == True
    ).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check access permissions
    if not file_record.is_public and file_record.uploaded_by_id != current_user.id:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    return file_record


@router.get("/{file_id}/download")
def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Download a file"""
    file_record = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.is_active == True
    ).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check access permissions
    if not file_record.is_public and file_record.uploaded_by_id != current_user.id:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    # Check if file exists on disk
    if not os.path.exists(file_record.file_path):
        logger.error(f"File not found on disk: {file_record.file_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    
    return FileResponse(
        file_record.file_path,
        media_type=file_record.mime_type,
        filename=file_record.original_filename
    )


@router.delete("/{file_id}")
def delete_file(
    file_id: int,
    permanent: bool = Query(False, description="Permanently delete file from disk"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a file (soft delete by default)"""
    file_record = db.query(FileModel).filter(FileModel.id == file_id).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check permissions (only owner or admin can delete)
    if file_record.uploaded_by_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the file owner or admin can delete this file"
        )
    
    if permanent:
        # Delete file from disk
        if os.path.exists(file_record.file_path):
            try:
                os.remove(file_record.file_path)
                logger.info(f"File permanently deleted from disk: {file_record.file_path}")
            except Exception as e:
                logger.error(f"Failed to delete file from disk: {e}")
        
        # Delete from database
        db.delete(file_record)
    else:
        # Soft delete
        file_record.is_active = False
    
    db.commit()
    
    logger.info(f"File {file_id} deleted by {current_user.username} (permanent: {permanent})")
    
    return {"message": f"File {'permanently' if permanent else 'soft'} deleted"}


@router.post("/{file_id}/verify")
def verify_file_integrity(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Verify file integrity using hash"""
    file_record = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.is_active == True
    ).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    if not os.path.exists(file_record.file_path):
        return {
            "valid": False,
            "message": "File not found on disk"
        }
    
    # Calculate current hash
    current_hash = calculate_file_hash(file_record.file_path)
    
    # Compare with stored hash
    is_valid = current_hash == file_record.file_hash
    
    return {
        "valid": is_valid,
        "original_hash": file_record.file_hash,
        "current_hash": current_hash,
        "message": "File integrity verified" if is_valid else "File has been modified"
    }


@router.get("/stats/summary")
def get_file_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get file storage statistics"""
    total_files = db.query(FileModel).filter(FileModel.is_active == True).count()
    
    total_size = db.query(
        db.func.sum(FileModel.file_size)
    ).filter(FileModel.is_active == True).scalar() or 0
    
    files_by_category = db.query(
        FileCategory.name,
        db.func.count(FileModel.id),
        db.func.sum(FileModel.file_size)
    ).join(
        FileModel, FileCategory.id == FileModel.category_id
    ).filter(
        FileModel.is_active == True
    ).group_by(FileCategory.name).all()
    
    files_by_type = db.query(
        FileModel.file_extension,
        db.func.count(FileModel.id)
    ).filter(
        FileModel.is_active == True
    ).group_by(FileModel.file_extension).all()
    
    return {
        "total_files": total_files,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "by_category": [
            {
                "category": cat[0],
                "count": cat[1],
                "size_bytes": cat[2] or 0
            }
            for cat in files_by_category
        ],
        "by_type": [
            {
                "extension": ext[0],
                "count": ext[1]
            }
            for ext in files_by_type
        ]
    }